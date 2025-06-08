from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
import os

os.environ[
    "OPENAI_API_KEY"] = "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"

loader = TextLoader("data/graham_chunks.txt")
docs = loader.load()

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "graham_db"))

db = Chroma.from_documents(docs, embedding=OpenAIEmbeddings(), persist_directory=db_path)
db.persist()
