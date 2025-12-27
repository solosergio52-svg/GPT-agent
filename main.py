import os
import csv
import io
from typing import List, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Buildeco Parser Service", version="0.1.0")

REGISTRY: List[Dict[str, Any]] = []


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


async def load_registry() -> List[Dict[str, Any]]:
    url = _env("OBJECTS_REGISTRY_CSV_URL")

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"Registry CSV download failed: {r.status_code}")

    content = r.text
    reader = csv.DictReader(io.StringIO(content))

    required = {"object_name", "folder_url"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise RuntimeError(f"Registry CSV must contain columns: {sorted(required)}")

    items: List[Dict[str, Any]] = []
    for row in reader:
        name = (row.get("object_name") or "").strip()
        folder = (row.get("folder_url") or "").strip()
        if not name or not folder:
            continue
        items.append({"object_name": name, "folder_url": folder})

    return items


@app.on_event("startup")
async def startup():
    global REGISTRY
    REGISTRY = await load_registry()


@app.get("/health")
async def health():
    return {"ok": True, "objects": len(REGISTRY)}


@app.get("/objects")
async def get_objects():
    return {"items": REGISTRY}


@app.post("/reload")
async def reload_registry():
    # можно убрать этот эндпоинт позже или закрыть авторизацией
    global REGISTRY
    REGISTRY = await load_registry()
    return {"ok": True, "objects": len(REGISTRY)}
