from langchain.llms import OpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from backend.agents.agent import retriever

llm = OpenAI(temperature=0)
chain = load_qa_with_sources_chain(llm, chain_type="stuff")


def answer_question(query):
    docs = retriever.get_relevant_documents(query)
    response = chain({"input_documents": docs, "question": query}, return_only_outputs=True)
    return response["output_text"]


answer_question("Who is the founder of the growth investing philosophy?")  # Example usage