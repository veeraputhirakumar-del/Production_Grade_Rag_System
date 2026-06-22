from bm25_store import bm25_store
from chroma_store import chroma_store


def hybrid_search(query, semantic_k=8, bm25_k=8, final_k=5):
    """Combine vector and keyword rankings with reciprocal-rank fusion."""
    semantic_results = chroma_store.semantic_search(query, top_k=semantic_k)
    keyword_results = bm25_store.keyword_search(query, top_k=bm25_k)
    combined = {}

    for source_type, weight, results in (
        ("semantic", 0.65, semantic_results),
        ("bm25", 0.35, keyword_results),
    ):
        for rank, result in enumerate(results, start=1):
            chroma_id = result["chroma_id"]
            item = combined.setdefault(
                chroma_id,
                {
                    **result,
                    "semantic_score": 0.0,
                    "bm25_score": 0.0,
                    "final_score": 0.0,
                    "matched_by": [],
                },
            )
            raw_score = max(float(result.get("score") or 0), 0.0)
            item[f"{source_type}_score"] = raw_score
            item["final_score"] += weight / rank
            item["matched_by"].append(source_type)

    ranked = sorted(
        combined.values(),
        key=lambda item: item["final_score"],
        reverse=True,
    )
    for item in ranked:
        item["source_type"] = "+".join(item.pop("matched_by"))
    return ranked[:final_k]
