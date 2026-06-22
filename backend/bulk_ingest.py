import argparse
import json
import sys

from bulk_ingestion import ingest_documents_from_directory
from config import BULK_DOCUMENT_DIR


def print_progress(event):
    position = event["position"]
    total = event["total"]
    filename = event["filename"]
    stage = event["stage"]
    if stage == "processing":
        print(f"[{position}/{total}] Processing {filename}...", flush=True)
    elif stage == "processed":
        chunks = event["result"].get("total_chunks", 0)
        print(f"[{position}/{total}] Processed {filename} ({chunks} chunks)", flush=True)
    elif stage == "skipped":
        print(f"[{position}/{total}] Skipped duplicate {filename}", flush=True)
    else:
        print(f"[{position}/{total}] Failed {filename}: {event.get('error')}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Bulk-ingest documents into SQLite, ChromaDB, and BM25."
    )
    parser.add_argument(
        "--folder",
        default=BULK_DOCUMENT_DIR,
        help=f"Folder to scan recursively (default: {BULK_DOCUMENT_DIR})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final summary as JSON.",
    )
    args = parser.parse_args()

    try:
        summary = ingest_documents_from_directory(
            args.folder,
            progress_callback=None if args.json else print_progress,
        )
    except Exception as error:
        print(f"Bulk ingestion could not start: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("\nBulk ingestion complete")
        print(f"Found:     {summary['total_found']}")
        print(f"Processed: {summary['processed']}")
        print(f"Skipped:   {summary['skipped']}")
        print(f"Failed:    {summary['failed']}")
        print(f"Chunks:    {summary['total_chunks']}")
        print(f"BM25:      {'rebuilt' if summary['bm25_rebuilt'] else 'unchanged'}")
        if summary.get("bm25_error"):
            print(f"BM25 error: {summary['bm25_error']}")

    return 1 if summary["failed"] or summary.get("bm25_error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
