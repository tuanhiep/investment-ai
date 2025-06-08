import os

if __name__ == "__main__":
    os.environ[
        "OPENAI_API_KEY"] = "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"

    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "backend/main.py"))
    os.system("streamlit run " + app_path)
