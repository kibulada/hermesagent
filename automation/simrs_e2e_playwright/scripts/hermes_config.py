#!/usr/bin/env python3
"""
hermes_config.py — baca token dari Hermes config.yaml (single source of truth).
Sesuai AGENTS.md §9.5 (no hardcode, no echo).

Path:
    - Windows default: C:\\Users\\ASUS\\AppData\\Local\\hermes\\config.yaml
    - Override via HERMES_CONFIG_PATH env var

Resolution order (per pipeline env var):
    1. os.environ[name] (override manual)
    2. config.yaml lewat mapping table
    3. None (kalau dua-duanya kosong)

Usage:
    from hermes_config import get_token
    token = get_token('OP_API_TOKEN')  # str | None
"""
import os
import sys
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG_PATH = Path(os.environ.get('LOCALAPPDATA', '')) / 'hermes' / 'config.yaml'
CUSTOM_ENV_PATH = Path(os.environ.get('HERMES_CUSTOM_ENV', 'D:/Hermes-QA/config/.env'))

# Mapping: pipeline env var -> (config.yaml path)
TOKEN_MAP = {
    'OP_API_TOKEN': ('mcp_servers', 'openproject', 'env', 'OPENPROJECT_API_KEY'),
    'OP_BASE_URL': ('mcp_servers', 'openproject', 'env', 'OPENPROJECT_URL'),
    'GITLAB_TOKEN': ('mcp_servers', 'gitlab', 'env', 'GITLAB_TOKEN'),
    'GITLAB_URL': ('mcp_servers', 'gitlab', 'env', 'GITLAB_URL'),
}

# custom_providers adalah list, bukan dict, jadi tidak bisa lewat TOKEN_MAP.
# Mapping: pipeline env var -> (nama provider, field di entry provider).
PROVIDER_MAP = {
    'HERMES_API_KEY': ('hermes', 'api_key'),
    'HERMES_API_URL': ('hermes', 'base_url'),
}


def _resolve_provider(config: dict, provider_name: str, field: str):
    """Ambil field dari custom_providers[name == provider_name]."""
    providers = config.get('custom_providers')
    if not isinstance(providers, list):
        return None
    for entry in providers:
        if isinstance(entry, dict) and entry.get('name') == provider_name:
            value = entry.get(field)
            return str(value) if value else None
    return None

_env_cache: Optional[dict] = None
_env_loaded: bool = False

_cache: Optional[dict] = None
_load_failed: bool = False


def _config_path() -> Path:
    override = os.environ.get('HERMES_CONFIG_PATH')
    return Path(override) if override else DEFAULT_CONFIG_PATH


def _load_config() -> Optional[dict]:
    """Load config.yaml 1x, cache result. Return None kalau gagal."""
    global _cache, _load_failed
    if _cache is not None or _load_failed:
        return _cache

    path = _config_path()
    if not path.exists():
        _load_failed = True
        return None

    try:
        import yaml  # noqa: F401  # PyYAML
        with open(path, 'r', encoding='utf-8') as f:
            _cache = yaml.safe_load(f) or {}
        return _cache
    except Exception:
        _load_failed = True
        return None


def _resolve_yaml_path(data: dict, path: tuple) -> Optional[str]:
    """Walk nested dict via tuple path. Return None kalau key missing."""
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return str(node) if node is not None else None


def _load_env_file() -> dict:
    """Load D:\\Hermes-QA\\config\\.env. Cache 1x. Return empty dict kalau gagal."""
    global _env_cache, _env_loaded
    if _env_loaded:
        return _env_cache or {}

    _env_loaded = True
    if not CUSTOM_ENV_PATH.exists():
        _env_cache = {}
        return {}

    result: dict = {}
    try:
        for raw_line in CUSTOM_ENV_PATH.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            result[key.strip()] = value.strip()
    except OSError:
        result = {}

    _env_cache = result
    return result


def get_token(name: str) -> Optional[str]:
    """
    Resolve token untuk pipeline env var name.
    Priority: os.environ > config.yaml > config/.env.
    Return None kalau tiga-tiganya kosong.
    """
    env_val = os.environ.get(name)
    if env_val:
        return env_val

    if name in TOKEN_MAP:
        config = _load_config()
        if config is not None:
            yaml_val = _resolve_yaml_path(config, TOKEN_MAP[name])
            if yaml_val:
                return yaml_val

    if name in PROVIDER_MAP:
        config = _load_config()
        if config is not None:
            provider_name, field = PROVIDER_MAP[name]
            provider_val = _resolve_provider(config, provider_name, field)
            if provider_val:
                if name == 'HERMES_API_URL' and not provider_val.rstrip('/').endswith('/chat/completions'):
                    provider_val = provider_val.rstrip('/') + '/chat/completions'
                return provider_val

    custom_env = _load_env_file()
    return custom_env.get(name)
