# Bulk document ingestion

## Required document path

The default configuration expects the raw documents here:

```text
rag-system/streamlit_frontend/data/documents
```

If your folders differ, set `BULK_DOCUMENT_DIR` in the backend `.env` to the
correct absolute path. Evidence can only be generated from documents that
have completed ingestion into ChromaDB and BM25.

With the project structure above, set:

```env
BULK_DOCUMENT_DIR=../streamlit_frontend/data/documents
```

If you instead keep the documents inside the backend folder, use:

```env
BULK_DOCUMENT_DIR=data/documents
```

Other optional `.env` settings:

```env
EMBEDDING_BATCH_SIZE=32
CHROMA_BATCH_SIZE=128
```

The scanner searches that folder recursively and accepts PDF, DOCX, TXT, MD,
and CSV files.

## Install the DOCX dependency

```bash
pip install python-docx
```

## Run from the backend project folder

Stop FastAPI before running the first bulk job so ChromaDB has only one writer:

```bash
python bulk_ingest.py
```

After the backend is running, ingestion can also be started through FastAPI:

```bash
curl -X POST http://localhost:8000/documents/bulk-ingest
```

Confirm that `total_found` is `50`, `failed` is `0`, and `processed + skipped`
is `50`. Restart the backend before testing questions if it was already open.

To specify a different folder:

```bash
python bulk_ingest.py --folder "data/documents"
```

The command:

1. Migrates the existing SQLite schema by adding `documents.file_hash`.
2. Backfills hashes for existing document paths when possible.
3. Skips content that was already processed.
4. Parses and chunks each new document.
5. Inserts each document's chunks in one SQLite transaction.
6. Embeds and upserts vectors into ChromaDB in bounded batches.
7. Rebuilds BM25 once after all new documents finish.
8. Prints a processed/skipped/failed summary.

Rerunning the command is safe: processed documents with identical content are
reported as skipped.

## Optional FastAPI trigger

After the backend is running, the same configured folder can be ingested with:

```bash
curl -X POST http://localhost:8000/documents/bulk-ingest
```

For the initial 50-document job, prefer the CLI because it is not subject to an
HTTP client timeout.
