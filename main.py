import os
import csv
import io
from typing import List, Dict, Any

import httpx
from fastapi import FastAPI
from PyPDF2 import PdfReader
import docx

app = FastAPI(title="Buildeco Correspondence API", version="1.1.0")

REGISTRY: List[Dict[str, Any]] = []
YANDEX_API = "https://cloud-api.yandex.net/v1/disk"


# === Утилиты ===
def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


# === Загрузка CSV реестра ===
async def load_registry() -> List[Dict[str, Any]]:
    url = _env("OBJECTS_REGISTRY_CSV_URL")
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.get(url)
    r.raise_for_status()

    reader = csv.DictReader(io.StringIO(r.text))
    required = {"object_name", "folder_url"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise RuntimeError(f"Registry CSV must contain columns: {sorted(required)}")

    items = []
    for row in reader:
        name = (row.get("object_name") or "").strip()
        folder = (row.get("folder_url") or "").strip()
        if not name or not folder:
            continue
        items.append({"object_name": name, "folder_url": folder})
    return items


# === Работа с Яндекс.Диском ===
async def yadisk_request(method: str, path: str, params=None) -> Dict[str, Any]:
    headers = {"Authorization": f"OAuth {_env('YANDEX_DISK_TOKEN')}"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.request(method, f"{YANDEX_API}{path}", headers=headers, params=params)
    r.raise_for_status()
    return r.json()


async def list_files_by_public_url(folder_url: str) -> List[Dict[str, Any]]:
    public_key = folder_url.strip()
    data = await yadisk_request("GET", "/public/resources", params={"public_key": public_key, "limit": 1000})
    return data.get("_embedded", {}).get("items", [])


async def download_file_from_public(folder_url: str, file_path: str) -> bytes:
    public_key = folder_url.strip()
    params = {"public_key": public_key, "path": file_path}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        r = await client.get(f"{YANDEX_API}/public/resources/download", params=params)
    r.raise_for_status()
    href = r.json().get("href")
    if not href:
        raise RuntimeError("Download link not found")

    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        file_response = await client.get(href)
    file_response.raise_for_status()
    return file_response.content


# === Извлечение текста из файлов ===
def extract_text_from_pdf(content: bytes) -> str:
    temp_path = "/tmp/temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(content)
    reader = PdfReader(temp_path)
    return "\n".join([page.extract_text() or "" for page in reader.pages])


def extract_text_from_docx(content: bytes) -> str:
    temp_path = "/tmp/temp.docx"
    with open(temp_path, "wb") as f:
        f.write(content)
    doc = docx.Document(temp_path)
    return "\n".join(p.text for p in doc.paragraphs)


# === API ===
@app.on_event("startup")
async def startup():
    global REGISTRY
    REGISTRY = await load_registry()


@app.get("/health")
async def health():
    return {"ok": True, "objects": len(REGISTRY)}


@app.get("/objects")
async def get_objects():
    """Показать все проекты, где есть переписка"""
    return {"items": REGISTRY}


@app.get("/objects/{object_name}/fulltext")
async def get_fulltext(object_name: str, limit: int = 5, offset: int = 0):
    """Загрузить полный текст всех писем по объекту (с постраничной выборкой)"""
    obj = next((o for o in REGISTRY if o["object_name"] == object_name), None)
    if not obj:
        return {"error": "object not found", "object_name": object_name}

    folder_url = obj["folder_url"]
    files = await list_files_by_public_url(folder_url)
    files = [f for f in files if f["name"].lower().endswith((".pdf", ".docx"))]

    total = len(files)
    files = files[offset:offset + limit]
    results = []

    for f in files:
        try:
            content = await download_file_from_public(folder_url, f["path"])
            text = extract_text_from_pdf(content) if f["name"].lower().endswith(".pdf") else extract_text_from_docx(content)
            results.append({
                "file_name": f["name"],
                "modified": f.get("modified"),
                "text": text
            })
        except Exception as e:
            results.append({"file_name": f["name"], "error": str(e)})

    return {"object_name": object_name, "total_files": total, "limit": limit, "offset": offset, "files": results}
