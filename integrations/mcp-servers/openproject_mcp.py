#!/usr/bin/env python3
"""OpenProject READ-ONLY MCP server.

Exposes a small, strictly read-only surface over the OpenProject REST API v3
(https://tracker.kesia.id). Every tool issues only HTTP GET — there is NO tool
that creates, updates, or deletes anything. Auth is HTTP Basic ("apikey":<key>).

Config via env:
  OPENPROJECT_URL       base url, e.g. https://tracker.kesia.id
  OPENPROJECT_API_KEY   API key (from OpenProject > My Account > Access tokens)
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

BASE = os.environ.get("OPENPROJECT_URL", "https://tracker.kesia.id").rstrip("/")
API_KEY = os.environ.get("OPENPROJECT_API_KEY", "")

mcp = FastMCP("openproject")


def _client() -> httpx.Client:
    if not API_KEY:
        raise RuntimeError("OPENPROJECT_API_KEY not set")
    return httpx.Client(
        base_url=BASE,
        auth=("apikey", API_KEY),
        timeout=30.0,
        headers={"Accept": "application/json"},
    )


def _get(path: str, params: Optional[dict] = None) -> dict:
    """GET only. Any non-2xx raises with a short message."""
    with _client() as c:
        r = c.get(path, params=params or {})
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code} on {path}: {r.text[:300]}")
    return r.json()


def _link_title(obj: dict, key: str) -> Optional[str]:
    try:
        return obj.get("_links", {}).get(key, {}).get("title")
    except Exception:
        return None


def _wp_summary(wp: dict) -> dict:
    """Trim a work package to the fields that matter (avoid huge payloads)."""
    return {
        "id": wp.get("id"),
        "subject": wp.get("subject"),
        "type": _link_title(wp, "type"),
        "status": _link_title(wp, "status"),
        "priority": _link_title(wp, "priority"),
        "project": _link_title(wp, "project"),
        "assignee": _link_title(wp, "assignee"),
        "author": _link_title(wp, "author"),
        "updatedAt": wp.get("updatedAt"),
    }


@mcp.tool()
def current_user() -> str:
    """Siapa pemilik API key ini (verifikasi koneksi OpenProject)."""
    u = _get("/api/v3/users/me")
    return json.dumps({"id": u.get("id"), "name": u.get("name"), "email": u.get("email"), "status": u.get("status")}, ensure_ascii=False)


@mcp.tool()
def list_projects(limit: int = 50) -> str:
    """List project di OpenProject (id, nama, identifier)."""
    data = _get("/api/v3/projects", {"pageSize": max(1, min(limit, 100))})
    els = data.get("_embedded", {}).get("elements", [])
    out = [{"id": p.get("id"), "name": p.get("name"), "identifier": p.get("identifier"), "active": p.get("active")} for p in els]
    return json.dumps({"total": data.get("total"), "projects": out}, ensure_ascii=False)


_STATUS_CACHE: dict[str, str] = {}
_ME_ID: Optional[str] = None


def _status_id(name_or_id: str) -> Optional[str]:
    """Resolve status name (case-insensitive) → id. Passthrough kalau udah id/None."""
    if not name_or_id:
        return None
    s = str(name_or_id).strip()
    if s.isdigit():
        return s
    global _STATUS_CACHE
    if not _STATUS_CACHE:
        for st in _get("/api/v3/statuses", {"pageSize": 100}).get("_embedded", {}).get("elements", []):
            _STATUS_CACHE[str(st.get("name", "")).lower()] = str(st.get("id"))
    return _STATUS_CACHE.get(s.lower())


def _me_id() -> str:
    global _ME_ID
    if _ME_ID is None:
        _ME_ID = str(_get("/api/v3/users/me").get("id"))
    return _ME_ID


def _query_wps(project_id: Optional[int], filters: list, limit: int) -> str:
    params: dict[str, Any] = {"pageSize": max(1, min(limit, 100)), "sortBy": '[["updatedAt","desc"]]'}
    if filters:
        params["filters"] = json.dumps(filters)
    path = f"/api/v3/projects/{project_id}/work_packages" if project_id else "/api/v3/work_packages"
    data = _get(path, params)
    els = data.get("_embedded", {}).get("elements", [])
    return json.dumps({"total": data.get("total"), "count": len(els), "work_packages": [_wp_summary(w) for w in els]}, ensure_ascii=False)


@mcp.tool()
def list_work_packages(project_id: Optional[int] = None, search: Optional[str] = None, status: Optional[str] = None, assignee: Optional[str] = None, only_open: bool = True, limit: int = 25) -> str:
    """List/cari work package (task). Filter opsional: project_id (default: semua; kerjaan user di project 3 Kesia Dev), search (teks), status (nama/id, mis. 'In progress'), assignee ('me' atau user id), only_open (default True; diabaikan kalau status diisi). Read-only."""
    filters: list[dict] = []
    if status:
        sid = _status_id(status)
        if sid:
            filters.append({"status": {"operator": "=", "values": [sid]}})
    elif only_open:
        filters.append({"status": {"operator": "o", "values": []}})
    if assignee:
        aid = _me_id() if str(assignee).lower() in ("me", "gw", "saya") else str(assignee)
        filters.append({"assignee": {"operator": "=", "values": [aid]}})
    if search:
        filters.append({"search": {"operator": "**", "values": [search]}})
    return _query_wps(project_id, filters, limit)


@mcp.tool()
def my_work_packages(project_id: Optional[int] = 3, status: Optional[str] = None, only_open: bool = True, limit: int = 25) -> str:
    """Task yg di-assign ke user (pemilik API key). Default project 3 = Kesia Dev (kerjaan utama user). Opsional filter status (nama/id). Read-only."""
    filters: list[dict] = [{"assignee": {"operator": "=", "values": [_me_id()]}}]
    if status:
        sid = _status_id(status)
        if sid:
            filters.append({"status": {"operator": "=", "values": [sid]}})
    elif only_open:
        filters.append({"status": {"operator": "o", "values": []}})
    return _query_wps(project_id, filters, limit)


@mcp.tool()
def get_work_package(id: int) -> str:
    """Detail satu work package (termasuk deskripsi). Read-only."""
    wp = _get(f"/api/v3/work_packages/{id}")
    s = _wp_summary(wp)
    desc = wp.get("description") or {}
    s["description"] = desc.get("raw") if isinstance(desc, dict) else None
    s["startDate"] = wp.get("startDate")
    s["dueDate"] = wp.get("dueDate")
    s["percentageDone"] = wp.get("percentageDone")
    return json.dumps(s, ensure_ascii=False)


@mcp.tool()
def list_statuses() -> str:
    """List status yang tersedia (buat rujukan filter)."""
    data = _get("/api/v3/statuses")
    els = data.get("_embedded", {}).get("elements", [])
    return json.dumps([{"id": s.get("id"), "name": s.get("name"), "isClosed": s.get("isClosed")} for s in els], ensure_ascii=False)


@mcp.tool()
def list_types() -> str:
    """List type work package (Task, Bug, Feature, dll)."""
    data = _get("/api/v3/types")
    els = data.get("_embedded", {}).get("elements", [])
    return json.dumps([{"id": t.get("id"), "name": t.get("name")} for t in els], ensure_ascii=False)


@mcp.tool()
def list_boards(project_identifier: str = "kesia") -> str:
    """List board (grid) di sebuah project. Default 'kesia' (Kesia Dev). Board manual, jadi isi kolomnya baca via list_work_packages by status. Read-only."""
    data = _get("/api/v3/grids", {"pageSize": 100})
    els = data.get("_embedded", {}).get("elements", [])
    scope = f"/projects/{project_identifier}/boards"
    out = []
    for g in els:
        href = (g.get("_links", {}).get("scope", {}) or {}).get("href", "")
        name = g.get("name")
        if href == scope and name and not str(name).startswith("[OLD]"):
            out.append({"id": g.get("id"), "name": name})
    return json.dumps(out, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
