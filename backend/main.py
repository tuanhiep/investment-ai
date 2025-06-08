import streamlit as st
from langchain.llms import OpenAI

from backend.services.query_service import answer_question
import os

os.environ[
    "OPENAI_API_KEY"] = "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"

# Initialize the language model
llm = OpenAI(temperature=0)

st.title("Ask Benjamin Graham – Khí Học")

st.markdown("""
Before asking, take a breath.
Graham only responds to questions asked with discipline and clarity.

> *“Investment is most intelligent when it is most businesslike.”*
""")

query = st.text_input("Your investment question:")

if query:
    result = answer_question(query)
    st.write(result)
