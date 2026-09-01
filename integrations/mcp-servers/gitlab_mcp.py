#!/usr/bin/env python3
"""GitLab READ-ONLY MCP server.

Read-only surface over the GitLab REST API v4 (gitlab.com). Every tool issues
only HTTP GET — NO tool creates/updates/deletes/merges anything. Auth via
PRIVATE-TOKEN header (read_api / read_repository scopes).

Env:
  GITLAB_URL     base url (default https://gitlab.com)
  GITLAB_TOKEN   personal access token (read-only scopes)
"""
from __future__ import annotations

import base64
import json
import os
from urllib.parse import quote
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

BASE = os.environ.get("GITLAB_URL", "https://gitlab.com").rstrip("/")
TOKEN = os.environ.get("GITLAB_TOKEN", "")
API = f"{BASE}/api/v4"

mcp = FastMCP("gitlab")


def _get(path: str, params: Optional[dict] = None) -> Any:
    if not TOKEN:
        raise RuntimeError("GITLAB_TOKEN not set")
    with httpx.Client(timeout=30.0, headers={"PRIVATE-TOKEN": TOKEN, "Accept": "application/json"}) as c:
        r = c.get(f"{API}{path}", params=params or {})
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code} on {path}: {r.text[:300]}")
    return r.json()


def _pid(project: str) -> str:
    """Accept numeric id or namespace/path; URL-encode the path form."""
    p = str(project).strip()
    return p if p.isdigit() else quote(p, safe="")


def _issue(i: dict) -> dict:
    return {
        "iid": i.get("iid"), "title": i.get("title"), "state": i.get("state"),
        "labels": i.get("labels"), "assignees": [a.get("username") for a in i.get("assignees", [])],
        "author": (i.get("author") or {}).get("username"), "updated_at": i.get("updated_at"),
        "web_url": i.get("web_url"),
    }


def _mr(m: dict) -> dict:
    return {
        "iid": m.get("iid"), "title": m.get("title"), "state": m.get("state"),
        "draft": m.get("draft"), "source_branch": m.get("source_branch"), "target_branch": m.get("target_branch"),
        "author": (m.get("author") or {}).get("username"), "merge_status": m.get("merge_status"),
        "updated_at": m.get("updated_at"), "web_url": m.get("web_url"),
    }


def _trim_diff(diffs: list, max_files: int = 15, max_chars: int = 4000):
    """Ringkas list diff GitLab: batasi jumlah file + panjang tiap diff (biar payload ga meledak)."""
    out = []
    for d in (diffs or [])[:max_files]:
        diff = d.get("diff", "") or ""
        if len(diff) > max_chars:
            diff = diff[:max_chars] + "\n...[diff truncated]"
        out.append({
            "path": d.get("new_path"), "new_file": d.get("new_file"),
            "deleted": d.get("deleted_file"), "renamed": d.get("renamed_file"),
            "diff": diff,
        })
    return out, len(diffs or [])


@mcp.tool()
def current_user() -> str:
    """Siapa pemilik token (verifikasi koneksi GitLab)."""
    u = _get("/user")
    return json.dumps({"id": u.get("id"), "username": u.get("username"), "name": u.get("name")}, ensure_ascii=False)


@mcp.tool()
def list_projects(search: Optional[str] = None, limit: int = 30) -> str:
    """List project yg lo jadi member (opsional filter `search`). Return id + path."""
    params: dict[str, Any] = {"membership": "true", "per_page": max(1, min(limit, 100)), "order_by": "last_activity_at"}
    if search:
        params["search"] = search
    d = _get("/projects", params)
    return json.dumps([{"id": p.get("id"), "path": p.get("path_with_namespace"), "default_branch": p.get("default_branch"), "last_activity": p.get("last_activity_at")} for p in d], ensure_ascii=False)


@mcp.tool()
def get_project(project: str) -> str:
    """Detail project (by id atau path 'namespace/repo')."""
    p = _get(f"/projects/{_pid(project)}")
    return json.dumps({"id": p.get("id"), "path": p.get("path_with_namespace"), "description": p.get("description"), "default_branch": p.get("default_branch"), "star_count": p.get("star_count"), "web_url": p.get("web_url"), "open_issues": p.get("open_issues_count")}, ensure_ascii=False)


@mcp.tool()
def list_issues(project: str, state: str = "opened", search: Optional[str] = None, limit: int = 25) -> str:
    """List issue di project. state: opened|closed|all. Opsional `search`."""
    params: dict[str, Any] = {"state": state, "per_page": max(1, min(limit, 100)), "order_by": "updated_at"}
    if search:
        params["search"] = search
    d = _get(f"/projects/{_pid(project)}/issues", params)
    return json.dumps([_issue(i) for i in d], ensure_ascii=False)


@mcp.tool()
def get_issue(project: str, iid: int) -> str:
    """Detail satu issue (termasuk deskripsi) by internal iid."""
    i = _get(f"/projects/{_pid(project)}/issues/{iid}")
    out = _issue(i); out["description"] = i.get("description")
    return json.dumps(out, ensure_ascii=False)


@mcp.tool()
def list_merge_requests(project: str, state: str = "opened", search: Optional[str] = None, limit: int = 25) -> str:
    """List merge request. state: opened|closed|merged|all. Opsional `search`."""
    params: dict[str, Any] = {"state": state, "per_page": max(1, min(limit, 100)), "order_by": "updated_at"}
    if search:
        params["search"] = search
    d = _get(f"/projects/{_pid(project)}/merge_requests", params)
    return json.dumps([_mr(m) for m in d], ensure_ascii=False)


@mcp.tool()
def get_merge_request(project: str, iid: int) -> str:
    """Detail satu MR (deskripsi + ringkasan diff/changes) by iid."""
    m = _get(f"/projects/{_pid(project)}/merge_requests/{iid}")
    out = _mr(m); out["description"] = m.get("description")
    try:
        ch = _get(f"/projects/{_pid(project)}/merge_requests/{iid}/changes")
        files, total = _trim_diff(ch.get("changes", []))
        out["files_changed"] = total
        out["diffs"] = files
    except Exception:
        pass
    return json.dumps(out, ensure_ascii=False)


@mcp.tool()
def list_commits(project: str, ref: Optional[str] = None, limit: int = 20) -> str:
    """Commit terbaru di project (opsional `ref` branch/tag)."""
    params: dict[str, Any] = {"per_page": max(1, min(limit, 100))}
    if ref:
        params["ref_name"] = ref
    d = _get(f"/projects/{_pid(project)}/repository/commits", params)
    return json.dumps([{"short_id": c.get("short_id"), "title": c.get("title"), "author": c.get("author_name"), "created_at": c.get("created_at")} for c in d], ensure_ascii=False)


@mcp.tool()
def list_pipelines(project: str, limit: int = 15) -> str:
    """Pipeline CI terbaru (status, ref, sha)."""
    d = _get(f"/projects/{_pid(project)}/pipelines", {"per_page": max(1, min(limit, 100)), "order_by": "id", "sort": "desc"})
    return json.dumps([{"id": p.get("id"), "status": p.get("status"), "ref": p.get("ref"), "sha": (p.get("sha") or "")[:8], "web_url": p.get("web_url")} for p in d], ensure_ascii=False)


@mcp.tool()
def get_file(project: str, path: str, ref: Optional[str] = None) -> str:
    """Baca isi 1 file di repo (butuh scope read_repository). `path` relatif dari root repo."""
    params = {"ref": ref} if ref else {}
    d = _get(f"/projects/{_pid(project)}/repository/files/{quote(path, safe='')}", params)
    content = d.get("content")
    if content and d.get("encoding") == "base64":
        try:
            content = base64.b64decode(content).decode("utf-8", "replace")
        except Exception:
            pass
    # batasi biar ga kebanyakan
    if isinstance(content, str) and len(content) > 20000:
        content = content[:20000] + "\n...[truncated]"
    return json.dumps({"file": d.get("file_path"), "ref": d.get("ref"), "size": d.get("size"), "content": content}, ensure_ascii=False)


@mcp.tool()
def get_commit_diff(project: str, sha: str) -> str:
    """Diff/perubahan 1 commit (per file, diff beneran). `sha` = commit hash (short/full). Read-only."""
    commit = _get(f"/projects/{_pid(project)}/repository/commits/{sha}")
    diffs = _get(f"/projects/{_pid(project)}/repository/commits/{sha}/diff")
    files, total = _trim_diff(diffs if isinstance(diffs, list) else [])
    return json.dumps({"sha": commit.get("short_id"), "title": commit.get("title"), "author": commit.get("author_name"), "created_at": commit.get("created_at"), "stats": commit.get("stats"), "files_changed": total, "diffs": files}, ensure_ascii=False)


@mcp.tool()
def search_commits(project: str, query: str, limit: int = 20) -> str:
    """Cari commit by pesan/judul (mis. nomor ticket '7453' → nemu commit 'PP#7453 ...'). Read-only."""
    d = _get(f"/projects/{_pid(project)}/search", {"scope": "commits", "search": query, "per_page": max(1, min(limit, 50))})
    rows = d if isinstance(d, list) else []
    return json.dumps([{"short_id": c.get("short_id"), "title": c.get("title"), "author": c.get("author_name"), "created_at": c.get("created_at")} for c in rows], ensure_ascii=False)


@mcp.tool()
def compare_refs(project: str, from_ref: str, to_ref: str) -> str:
    """Diff antar 2 ref (branch/tag/commit): from_ref → to_ref. Read-only."""
    d = _get(f"/projects/{_pid(project)}/repository/compare", {"from": from_ref, "to": to_ref})
    files, total = _trim_diff(d.get("diffs", []))
    commits = [{"short_id": c.get("short_id"), "title": c.get("title")} for c in d.get("commits", [])]
    return json.dumps({"from": from_ref, "to": to_ref, "commits": commits, "files_changed": total, "diffs": files}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
