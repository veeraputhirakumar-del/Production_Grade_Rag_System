def chunk_text(text, chunk_size=500, overlap=80):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size - 1")

    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_pages(pages, chunk_size=500, overlap=80):
    all_chunks = []
    chunk_index = 0
    for page in pages:
        for chunk in chunk_text(
            page["text"],
            chunk_size=chunk_size,
            overlap=overlap,
        ):
            all_chunks.append({
                "chunk_index": chunk_index,
                "page_number": page["page_number"],
                "text": chunk,
            })
            chunk_index += 1
    return all_chunks

