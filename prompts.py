from langchain_core.prompts import PromptTemplate

# cuma QA_EVAL_PROMPT yang dipake di sini, MPASI_PROMPT tetep di app
QA_EVAL_PROMPT = PromptTemplate.from_template("""
Kamu adalah ahli gizi bayi yang menjawab pertanyaan orang tua seputar MPASI.

Konteks dari sumber terpercaya (gunakan ini sebagai acuan utama, bukan pengetahuan umum):
{context_block}

Pertanyaan: {question}

Jawab pertanyaan di atas berdasarkan konteks yang diberikan, dengan bahasa yang
jelas dan mudah dipahami orang tua. Jawab dalam bentuk teks biasa (bukan JSON),
1-3 paragraf singkat, dan jangan sertakan informasi yang tidak didukung oleh
konteks di atas.
""")