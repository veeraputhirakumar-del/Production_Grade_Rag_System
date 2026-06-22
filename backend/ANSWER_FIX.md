# Evidence appears, but the answer is "not found"

The evidence panel displays the highest-ranked chunks even when none contains
the requested fact. For the Coimbatore lead question, the required source is:

```text
01_site_ns-site-cbe-01.txt
```

Its answer is `Ananya Bose`.

## Apply and run

1. Merge these backend files into the FastAPI backend.
2. Set this in the backend `.env`:

   ```env
   BULK_DOCUMENT_DIR=../streamlit_frontend/data/documents
   ```

3. Stop FastAPI before the first bulk ingestion.
4. From the backend folder, run:

   ```bash
   python bulk_ingest.py
   ```

5. Confirm the summary reports `Found: 50`, `Failed: 0`, and `BM25: rebuilt`.
6. Restart the backend:

   ```bash
   uvicorn main:app --reload
   ```

7. Ask the question again. The first evidence result should be
   `01_site_ns-site-cbe-01.txt`, and the answer should identify Ananya Bose.

The corrected pipeline strips the frontend's answer-mode instruction before
searching, uses punctuation-aware BM25 tokens, retrieves five final chunks,
and sends all useful source text to Ollama with a stricter grounded prompt.
