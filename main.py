import os
import csv
import io
from typing import List, Dict, Any
from pathlib import Path

import httpx
from fastapi import FastAPI
from PyPDF2 import PdfReader
import docx

app = FastAPI(title="Buildeco Parser Service", version="0.3.0")

REGISTRY: List[Dict[str, Any]] = []
YANDEX_API = "https://cloud-api.yandex.net/v1/disk"


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


# === CSV РЕЕСТР ===
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


# === ЯНДЕКС.ДИСК API ===
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
    public_key = folder_url.strip()
    data = await yadisk_request(
        "GET",
        "/public/resources",
        params={"public_key": public_key, "limit": 1000},
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


# === ИЗВЛЕЧЕНИЕ ТЕКСТА ===
def extract_text_from_pdf(content: bytes) -> str:
    temp_path = "/tmp/temp.pdf"
    with open(temp_path, "wb") as f:
        f.write(content)

    text = ""
    with open(temp_path, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(content: bytes) -> str:
    temp_path = "/tmp/temp.docx"
    with open(temp_path, "wb") as f:
        f.write(content)
    doc = docx.Document(temp_path)
    return "\n".join(p.text for p in doc.paragraphs)


# === ENDPOINTS ===
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


@app.get("/objects/{object_name}/filetext")
async def get_file_text(object_name: str, name: str):
    obj = next((o for o in REGISTRY if o["object_name"] == object_name), None)
    if not obj:
        return {"error": "object not found", "object_name": object_name}

    folder_url = obj["folder_url"]
    files = await list_files_by_public_url(folder_url)
    file = next((f for f in files if f["name"] == name), None)
    if not file:
        return {"error": "file not found", "name": name}

    content = await download_file_from_public(folder_url, file["path"])

    text = ""
    if name.lower().endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif name.lower().endswith(".docx"):
        text = extract_text_from_docx(content)
    else:
        return {"error": "unsupported file type"}

    return {
        "object_name": object_name,
        "file_name": name,
        "text": text[:10000]  # ограничим вывод
    }
import re

def classify_text(text: str) -> Dict[str, Any]:
    """Простая эвристическая классификация письма"""
    t = text.lower()
    direction = "входящее" if "вх" in t or "уведомление" in t else "исходящее"
    topic = None
    if any(k in t for k in ["аванс", "оплата", "счет", "к оплате"]):
        topic = "финансы"
    elif any(k in t for k in ["готовность", "строеготовность", "работы", "график"]):
        topic = "ход работ"
    elif any(k in t for k in ["замечания", "акт", "претензия", "дефект"]):
        topic = "замечания/качество"
    elif any(k in t for k in ["согласование", "утверждение", "техно"]):
        topic = "согласование"
    else:
        topic = "прочее"

    risk = any(k in t for k in ["не можем", "невозможно", "срыв", "штраф", "расторжение"])

    return {"direction": direction, "topic": topic, "risk": bool(risk)}


@app.get("/objects/{object_name}/analyze")
async def analyze_file(object_name: str, name: str):
    obj = next((o for o in REGISTRY if o["object_name"] == object_name), None)
    if not obj:
        return {"error": "object not found", "object_name": object_name}

    folder_url = obj["folder_url"]
    files = await list_files_by_public_url(folder_url)
    file = next((f for f in files if f["name"] == name), None)
    if not file:
        return {"error": "file not found", "name": name}

    content = await download_file_from_public(folder_url, file["path"])

    text = ""
    if name.lower().endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif name.lower().endswith(".docx"):
        text = extract_text_from_docx(content)
    else:
        return {"error": "unsupported file type"}

    info = classify_text(text)
    return {
        "object_name": object_name,
        "file_name": name,
        "analysis": info,
        "preview": text[:800]
    }
