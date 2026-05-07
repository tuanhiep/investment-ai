from pathlib import Path

from backend.services.knowledge import load_knowledge, retrieve


def test_knowledge_retrieval_finds_margin_of_safety() -> None:
    knowledge_path = Path(__file__).resolve().parents[1] / "db" / "data" / "graham_chunks.txt"
    chunks = load_knowledge(knowledge_path)
    matches = retrieve("How should I think about margin of safety?", chunks)

    assert chunks
    assert matches
    assert matches[0][0].title == "Margin of Safety"
