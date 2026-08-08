import json
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

# STUB tetap diperlukan: bug ini ke-trigger dari import internal ragas.evaluation.py sendiri
# (baris `from ragas.llms import llm_factory`), jadi kepicu SEBELUM kita sempet milih
# mau pake metrics legacy atau collections — jadi tetep wajib ada meski balik ke legacy API
import types
_stub_vertexai = types.ModuleType("langchain_community.chat_models.vertexai")
class ChatVertexAI:
    pass
_stub_vertexai.ChatVertexAI = ChatVertexAI
sys.modules["langchain_community.chat_models.vertexai"] = _stub_vertexai

from dotenv import load_dotenv
from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
# CHANGED: balik ke legacy metrics (ragas.metrics, bukan .collections)
# soalnya collections + evaluate() ternyata masih ada bug (#2624) yang belum di-fix ragas
# legacy class ini INHERIT dari Metric base class, jadi lolos dari isinstance check yang bikin crash
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
# CHANGED: balik pake wrapper lama, karena legacy metrics emang didesain buat dipasangin ini
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

# CHANGED: balik pake ChatGoogleGenerativeAI (langchain), bukan google.generativeai murni
# nggak butuh genai.configure() atau GenerativeModel lagi, cukup ini doang
# embeddings = LangchainEmbeddingsWrapper(
#     GoogleGenerativeAIEmbeddings(
#         model="models/text-embedding-004",  # tetep pake model yang beda dari KB (gemini-embedding-001), sesuai keputusan sebelumnya
#         google_api_key=os.getenv("GEMINI_API_KEY"),
#     )
# )
# ALTERNATIF: uncomment ini kalo mau konsisten satu model gemini-embedding-001 di semua tempat
embeddings = LangchainEmbeddingsWrapper(
    GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=os.getenv("GEMINI_API_KEY"))
)

llm = LangchainLLMWrapper(
    ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
)

with open("eval_dataset_output.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

clean = [r for r in raw if r.get("answer") and r.get("contexts")]
print(f"Dataset loaded: {len(clean)}/{len(raw)} valid entries\n")

samples = [
    SingleTurnSample(
        user_input=r["question"],
        response=r["answer"],
        retrieved_contexts=r["contexts"],
        reference=r["ground_truth"],
    )
    for r in clean
]
dataset = EvaluationDataset(samples=samples)

# CHANGED: legacy metrics cukup dikasih llm doang, embeddings di-auto-detect dari evaluate() level
# strictness TETAP nggak di-set (pake default library), sesuai keputusan sebelumnya
metrics = [
    Faithfulness(llm=llm),
    # CHANGED: strictness=1. AnswerRelevancy defaultnya minta 3 candidate generation
    # sekaligus dalam 1 API call, tapi gemini-3.1-flash-lite nolak request kaya gitu
    AnswerRelevancy(llm=llm, strictness=1),
    ContextPrecision(llm=llm),
    ContextRecall(llm=llm),
]

# CHANGED: evaluate() legacy cukup dikasih embeddings, nggak perlu llm= lagi di sini
# (llm udah nempel di tiap metric masing-masing)
results = evaluate(dataset=dataset, metrics=metrics, embeddings=embeddings)

print("\n=== RAGAS Results ===")
print(results)

df = results.to_pandas()

# UNCHANGED dari fix sebelumnya: nempelin balik difficulty & source yang ilang pas lewat SingleTurnSample
df["difficulty"] = [r["difficulty"] for r in clean]
df["source"] = [r["source"] for r in clean]

df.to_csv("eval_results.csv", index=False, encoding="utf-8-sig")
print("\nPer-question results saved to eval_results.csv")