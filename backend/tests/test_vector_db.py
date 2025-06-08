from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
import os

os.environ[
    "OPENAI_API_KEY"] = "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"

loader = TextLoader("/backend/data/graham_chunks.txt")
documents = loader.load()

embedding = OpenAIEmbeddings()

db = Chroma.from_documents(
    documents,
    embedding,
    persist_directory="./chroma_db"
)

retriever = db.as_retriever()
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

query = "Ai là người sáng lập trường phái đầu tư tăng trưởng?"

result = qa_chain.invoke({"query": query})

print("Câu trả lời:", result["result"])
