import subprocess


if __name__ == "__main__":
    subprocess.run(
        ["uvicorn", "backend.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        check=False,
    )
