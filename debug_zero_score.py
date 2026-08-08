import json
import sys
import os
import asyncio
sys.stdout.reconfigure(encoding='utf-8')

# STUB tetap perlu ada, sama kaya di eval_run.py (bug ragas yang belum di-fix upstream)
import types
_stub_vertexai = types.ModuleType("langchain_community.chat_models.vertexai")
class ChatVertexAI:
    pass
_stub_vertexai.ChatVertexAI = ChatVertexAI
sys.modules["langchain_community.chat_models.vertexai"] = _stub_vertexai

from dotenv import load_dotenv
from ragas.metrics import ContextPrecision
from ragas.llms import LangchainLLMWrapper
from ragas.dataset_schema import SingleTurnSample
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import BaseCallbackHandler

load_dotenv()

# ADDED: custom callback biar keliatan mentahan prompt yang dikirim ke LLM judge
# dan mentahan response yang balik, SEBELUM ragas parse jadi angka skor
class DebugCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("\n" + "="*70)
        print("PROMPT DIKIRIM KE LLM JUDGE:")
        print("="*70)
        for p in prompts:
            print(p)

    def on_llm_end(self, response, **kwargs):
        print("\n" + "="*70)
        print("RESPONSE MENTAH DARI LLM JUDGE:")
        print("="*70)
        print(response)

    def on_llm_error(self, error, **kwargs):
        print("\n" + "="*70)
        print("ERROR DARI LLM JUDGE (kalo ada):")
        print("="*70)
        print(repr(error))

# CHANGED: ambil data pertanyaan yang score-nya 0 langsung dari eval_dataset_output.json
# (bukan re-type manual, biar teksnya persis sama kaya yang beneran dipake pas eval kemarin)
with open("eval_dataset_output.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

MATCH_SNIPPET = "Responsive feeding adalah praktik memberi makan"  # potongan unik dari ground_truth soal ini
target = next((r for r in raw if MATCH_SNIPPET in r["ground_truth"]), None)

if target is None:
    print("GAGAL: nggak nemu row yang cocok di eval_dataset_output.json, cek lagi MATCH_SNIPPET-nya")
    sys.exit(1)

print(f"Pertanyaan yang mau di-debug: {target['question']}")
print(f"Jumlah context yang diretrieve: {len(target['contexts'])}")

llm = LangchainLLMWrapper(
    ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
)

metric = ContextPrecision(llm=llm)

sample = SingleTurnSample(
    user_input=target["question"],
    response=target["answer"],
    retrieved_contexts=target["contexts"],
    reference=target["ground_truth"],
)

async def main():
    score = await metric.single_turn_ascore(sample, callbacks=[DebugCallback()])
    print("\n" + "="*70)
    print(f"SKOR AKHIR: {score}")
    print("="*70)

asyncio.run(main())
