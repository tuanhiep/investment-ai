from pathlib import Path
import unittest

from backend.services.knowledge_repository import load_knowledge, retrieve


class KnowledgeRetrievalTest(unittest.TestCase):
    def test_retrieve_returns_margin_of_safety_for_matching_query(self) -> None:
        knowledge_path = Path(__file__).resolve().parents[1] / "db" / "data" / "graham_chunks.txt"
        chunks = load_knowledge(knowledge_path)

        matches = retrieve("How should I think about margin of safety?", chunks)

        self.assertTrue(chunks)
        self.assertTrue(matches)
        self.assertEqual(matches[0][0].title, "Margin of Safety")


if __name__ == "__main__":
    unittest.main()
