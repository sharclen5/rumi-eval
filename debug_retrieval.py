import sys
sys.stdout.reconfigure(encoding='utf-8')

from retriever import vectorstore  # pinjem vectorstore yang udah ada, ga bikin baru

# pertanyaan Q13 yang score CP-nya 0.0
QUESTION = "Seberapa sering bayi usia 6-23 bulan harus mengonsumsi daging, ikan, atau telur menurut WHO?"

print("=" * 70)
print("1) TOP-5 NORMAL (sama kaya yang kepake di retriever.py, k=5)")
print("=" * 70)
# similarity_search_with_relevance_scores balikin (doc, score) — score-nya
# udah dinormalize 0-1, makin gede makin mirip
results_top5 = vectorstore.similarity_search_with_relevance_scores(QUESTION, k=5)
for doc, score in results_top5:
    src = doc.metadata.get("source", "unknown")
    print(f"score={score:.4f} | source={src}")
    print(f"  {doc.page_content[:120]}...")
    print()

print("=" * 70)
print("2) TOP-3 KHUSUS FILTER source = who")
print("=" * 70)
# ini yang penting: kita paksa search cuma di dalem WHO doc aja,
# jadi ketauan beneran WHO Rec 4a itu ada di DB apa kagak, dan
# skornya berapa dibanding yang di atas (yang kepilih beneran)
try:
    results_who = vectorstore.similarity_search_with_relevance_scores(
        QUESTION, k=3, filter={"source": "who"}
    )
    if not results_who:
        print("KOSONG — ga ada dokumen dengan metadata source=who ketemu sama sekali.")
        print("Kemungkinan besar: value metadata 'source' beda formatnya (misal path lengkap, bukan cuma nama file).")
    for doc, score in results_who:
        print(f"score={score:.4f}")
        print(f"  {doc.page_content[:200]}...")
        print()
except Exception as e:
    print(f"Filter gagal jalan: {e}")
    print("Coba cek dulu format metadata 'source' yang asli — lihat bagian 3 di bawah.")

print("=" * 70)
print("3) SAMPLE METADATA — biar tau format 'source' yang sebenernya kepake")
print("=" * 70)
# ambil beberapa dokumen random dari collection buat liat metadata['source']
# nilainya persis apa (nama file doang? path penuh? title chunk?)
sample = vectorstore.get(limit=10, include=["metadatas"])
for meta in sample["metadatas"]:
    print(meta)