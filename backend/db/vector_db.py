from backend.config.config import get_settings
from backend.services.knowledge import load_knowledge


def build_local_knowledge_index() -> int:
    settings = get_settings()
    return len(load_knowledge(settings.knowledge_file))


if __name__ == "__main__":
    print(f"Loaded {build_local_knowledge_index()} knowledge chunks.")
