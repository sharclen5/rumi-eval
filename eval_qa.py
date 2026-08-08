import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from retriever import retriever
# CHANGED: langsung import retriever tanpa relative import,
# karena eval_qa.py sekarang hidup di luar package FastAPI
from prompts import QA_EVAL_PROMPT

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def answer_question(question: str) -> dict:
    retrieved_docs = retriever.invoke(question)
    contexts = [doc.page_content for doc in retrieved_docs]

    context_block = "\n\n".join(
        f"[Sumber: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in retrieved_docs
    )

    prompt = QA_EVAL_PROMPT.format(
        context_block=context_block,
        question=question,
    )

    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    ).with_retry(stop_after_attempt=5)

    fallback_llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    ).with_retry(stop_after_attempt=5)

    llm = primary_llm.with_fallbacks([fallback_llm])
    response = llm.invoke(prompt)

    if isinstance(response.content, list):
        answer_text = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in response.content
        )
    else:
        answer_text = response.content

    return {
        "question": question,
        "answer": answer_text.strip(),
        "contexts": contexts,
    }