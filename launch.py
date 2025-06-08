import os

if __name__ == "__main__":
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "backend/main.py"))
    os.system("streamlit run " + app_path )