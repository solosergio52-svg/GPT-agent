import os
import csv
import io
from typing import List, Dict, Any

import httpx
from fastapi import FastAPI

app = FastAPI(title="Buildeco Parser Service", version="0.1.1")

REGISTRY: List[Dict[str, Any]] = []


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


async def load_registry() -> List[Dict[str, Any]]:
    url = _env("OBJECTS_REGISTRY_CSV_URL")

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(url)

    if r.status_code != 200:
        raise RuntimeError(f"Registry CSV download failed: {r.status_code}")

    reader = csv.DictReader(io.StringIO(r.text))

    required = {"object_name", "folder_url"}
    if not reader.fieldnames or not requ
