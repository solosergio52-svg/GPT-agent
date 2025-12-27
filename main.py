import os
import csv
import io
from typing import List, Dict, Any

from fastapi import FastAPI
import httpx

app = FastAPI(title="Buildeco Parser Service", version="0.2.0")

REGISTRY: List[Dict[str, Any]] = []

YANDEX_API = "https://cloud-api.yandex.net/v1/disk"


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
    if (not reader.fieldnames) or (not required.issubset(set(reader.fieldnames))):
        raise RuntimeError(f"Registry CSV must contain columns: {sorted(required)}")

    items: List[Dict[str, Any]] = []
    for row in reader:
        name = (row.get("object_name") or "").strip()
        folder = (row.get("folder_url") or "").strip()
        if not name or not folder:
            continue
        items.append({"object_name": name, "folder_url": folder})

    return items


async def yadisk_request(method: str, path: str, params=None) -> Dict[str, Any]:
    headers = {"Authorization": f"OAuth {_env('YANDEX_DISK_TOKEN')}"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.request(
            method=method,
            url=f"{YANDEX_API}{path}",
            headers=headers,
            params=params,
        )
    r.raise_for_status()
    return r.json()


async def list_files_by_public_url(folder_url: str) -> List[Dict[str, Any]]:
    # Для Яндекс.Диска public_key может быть самой ссылкой.
    public_key = folder_url.strip()

    data = await yadisk_request(
        "GET",
        "/public/resources",
        params={
            "public_key": public_key,
            "limit": 1000,
        },
    )

    items = data.get("_embedded", {}).get("items", [])
    files: List[Dict[str, Any]] = []
    for i in items:
        if i.get("type") != "file":
            continue
        files.append(
            {
                "name": i.get("name"),
                "type": i.get("type"),
                "path": i.get("path"),
                "modified": i.get("modified"),
                "size": i.get("size"),
                "mime_type": i.get("mime_type"),
            }
        )
    return files


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
    global REGISTRY
    REGISTRY = await load_registry()
    return {"ok": True, "objects": len(REGISTRY)}


@app.get("/objects/{object_name}/files")
async def get_object_files(object_name: str):
    obj = next((o for o in REGISTRY if o["object_name"] == object_name), None)
    if not obj:
        return {"error": "object not found", "object_name": object_name}

    files = await list_files_by_public_url(obj["folder_url"])
    return {"object_name": object_name, "files": files}
