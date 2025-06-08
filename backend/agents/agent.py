import os

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from backend.agents.prompt_graham import graham_prompt

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db/graham_db"))
db = Chroma(persist_directory=db_path, embedding_function=OpenAIEmbeddings())
retriever = db.as_retriever()

llm = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo")

# If graham_prompt is a string, wrap it:
graham_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=graham_prompt
)

graham_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": graham_prompt}
)
