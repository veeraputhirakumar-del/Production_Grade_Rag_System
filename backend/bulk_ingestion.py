from pathlib import Path

from bm25_store import bm25_store
from database import init_db
from document_parser import SUPPORTED_EXTENSIONS
from rag_pipeline import hash_file, ingest_document


def discover_documents(folder):
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Document folder does not exist: {root}")
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def ingest_documents_from_directory(folder, progress_callback=None):
    init_db()
    files = discover_documents(folder)
    summary = {
        "folder": str(Path(folder).expanduser().resolve()),
        "total_found": len(files),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "total_chunks": 0,
        "bm25_rebuilt": False,
        "results": [],
    }

    for position, file_path in enumerate(files, start=1):
        event = {
            "position": position,
            "total": len(files),
            "filename": file_path.name,
        }
        if progress_callback:
            progress_callback({**event, "stage": "processing"})

        try:
            result = ingest_document(
                file_path=str(file_path),
                filename=file_path.name,
                rebuild_bm25=False,
                file_hash=hash_file(file_path),
            )
            if result["status"] == "skipped":
                summary["skipped"] += 1
            else:
                summary["processed"] += 1
                summary["total_chunks"] += int(result.get("total_chunks") or 0)
            summary["results"].append(result)
            if progress_callback:
                progress_callback({**event, "stage": result["status"], "result": result})
        except Exception as error:
            failure = {
                "filename": file_path.name,
                "status": "failed",
                "error": str(error),
            }
            summary["failed"] += 1
            summary["results"].append(failure)
            if progress_callback:
                progress_callback({**event, "stage": "failed", "error": str(error)})

    if files:
        try:
            bm25_store.rebuild()
            summary["bm25_rebuilt"] = True
        except Exception as error:
            summary["bm25_error"] = str(error)

    return summary
