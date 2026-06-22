import requests

from config import OLLAMA_MODEL, OLLAMA_URL


MAX_CONTEXT_CHARS = 6000
NOT_FOUND_ANSWER = "I could not find this information in the uploaded documents."


def build_prompt(question, contexts, answer_instruction=""):
    source_blocks = []
    used_chars = 0

    for index, item in enumerate(contexts, start=1):
        metadata = item.get("metadata") or {}
        chunk_text = str(item.get("text") or "").strip()
        if not chunk_text:
            continue

        block = (
            f"<source id=\"{index}\">\n"
            f"document: {metadata.get('filename', 'unknown')}\n"
            f"page: {metadata.get('page_number', 'unknown')}\n"
            f"content:\n{chunk_text}\n"
            "</source>"
        )
        remaining = MAX_CONTEXT_CHARS - used_chars
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining]
        source_blocks.append(block)
        used_chars += len(block)

    sources = "\n\n".join(source_blocks)
    style_instruction = (
        answer_instruction.strip()
        or "Answer normally using clear, concise language."
    )
    return f"""You answer questions from retrieved document excerpts.

Instructions:
- Read every source before deciding whether the answer is absent.
- When a source explicitly states the requested fact, answer it directly.
- Use only facts in the sources and cite the supporting source as [Source N].
- Do not reject an answer merely because other sources are less relevant.
- Only when none of the sources contains the requested fact, reply exactly:
  {NOT_FOUND_ANSWER}
- Keep the answer concise and clear.
- Presentation instruction: {style_instruction}

Question: {question.strip()}

Retrieved sources:
{sources}

Answer:"""


def _ollama_error(response):
    try:
        payload = response.json()
        if payload.get("error"):
            return str(payload["error"])
    except (TypeError, ValueError):
        pass
    return response.text.strip() or response.reason or "Unknown Ollama error"


def generate_answer(question, contexts, answer_instruction=""):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": build_prompt(question, contexts, answer_instruction),
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 250,
            "num_ctx": 4096,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=600)

        # Ollama commonly returns 500 when the model runner runs out of memory.
        # Retry once with a smaller context before reporting the server error.
        if response.status_code >= 500:
            retry_payload = {
                **payload,
                "options": {
                    **payload["options"],
                    "num_predict": 180,
                    "num_ctx": 2048,
                },
            }
            response = requests.post(
                OLLAMA_URL,
                json=retry_payload,
                timeout=600,
            )

        if not response.ok:
            return (
                f"LLM generation failed (Ollama HTTP {response.status_code}): "
                f"{_ollama_error(response)}"
            )

        response.raise_for_status()
        answer = str(response.json().get("response") or "").strip()
        return answer or "Ollama returned an empty response."
    except requests.exceptions.ConnectionError:
        return "LLM generation failed: Ollama is not running. Start it with `ollama serve`."
    except requests.exceptions.ReadTimeout:
        return "LLM generation failed: Ollama took too long to respond."
    except Exception as error:
        return f"LLM generation failed: {error}"
