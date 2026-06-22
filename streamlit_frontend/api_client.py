import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


def check_backend_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, "Backend is running"
        return False, f"Backend returned {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to backend"
    except Exception as error:
        return False, str(error)


def ask_question(question):
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question},
            timeout=600,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "success": True,
            "data": data,
            "answer": data.get("answer", "No answer found."),
            "sources": data.get("sources", []),
            "latency_ms": data.get("latency_ms"),
            "question_id": data.get("question_id"),
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to backend.",
            "answer": "",
            "sources": [],
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Backend took too long to respond.",
            "answer": "",
            "sources": [],
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "answer": "",
            "sources": [],
        }


def upload_document(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    try:
        response = requests.post(f"{API_URL}/upload", files=files, timeout=300)
        if response.status_code != 404:
            response.raise_for_status()
            return {"success": True, "data": response.json()}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend."}
    except Exception:
        pass

    try:
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            timeout=300,
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend."}
    except Exception as error:
        return {"success": False, "error": str(error)}


def get_documents():
    try:
        response = requests.get(f"{API_URL}/documents", timeout=20)
        response.raise_for_status()
        data = response.json()
        return {"success": True, "data": data.get("documents", [])}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend.", "data": []}
    except Exception as error:
        return {"success": False, "error": str(error), "data": []}


def get_document_details(document_id):
    try:
        response = requests.get(
            f"{API_URL}/documents/{document_id}/details",
            timeout=60,
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend.", "data": {}}
    except Exception as error:
        return {"success": False, "error": str(error), "data": {}}


def delete_document(document_id):
    try:
        response = requests.delete(f"{API_URL}/documents/{document_id}", timeout=20)
        if response.status_code == 404:
            return {
                "success": False,
                "error": "Delete endpoint is not available on the backend yet.",
            }
        response.raise_for_status()
        return {"success": True}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend."}
    except Exception as error:
        return {"success": False, "error": str(error)}


def get_question_history():
    try:
        response = requests.get(f"{API_URL}/history", timeout=20)
        if response.status_code != 404:
            response.raise_for_status()
            data = response.json()
            return {"success": True, "data": data.get("history", [])}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend.", "data": []}
    except Exception:
        pass

    try:
        response = requests.get(f"{API_URL}/questions/history", timeout=20)
        response.raise_for_status()
        data = response.json()
        return {"success": True, "data": data.get("questions", [])}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend.", "data": []}
    except Exception as error:
        return {"success": False, "error": str(error), "data": []}

