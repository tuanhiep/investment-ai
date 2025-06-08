import streamlit as st
from langchain.llms import OpenAI

from backend.services.query_service import answer_question
import os


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
