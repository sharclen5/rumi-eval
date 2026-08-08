import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

from eval_qa import answer_question

# Dataset mentah: 20 pertanyaan + ground truth
# Semua ground truth dijangkar langsung ke konten KB — tidak ada info eksternal
# Source legend:
#   [I-XX]  = langsung dari transkrip wawancara (Lembar_Wawancara_MPASI.md)
#   [KIA]   = dirangkum dari Buku_KIA_2024_MPASI_6-24_Bulan.md
#   [WHO]   = dirangkum dari WHO_Guideline.md
#   [Resep] = dirangkum dari Buku_Resep_MPASI.md

# CHANGED: rebuilt 20 questions with difficulty tiers (10 easy / 7 medium / 3 hard)
# and a "difficulty" field added for later per-tier RAGAS analysis
RAW_QUESTIONS = [

    # ── WHO GUIDELINE (6: 3 easy, 3 medium) ─────────────────────────

    {
        "question": "Pada usia berapa MPASI mulai diperkenalkan menurut WHO, dan apakah ASI tetap dilanjutkan?",
        "ground_truth": "WHO merekomendasikan MPASI diperkenalkan pada usia 6 bulan (180 hari) sambil tetap melanjutkan pemberian ASI. Ini adalah rekomendasi kuat meskipun didukung bukti dengan tingkat kepastian rendah.",
        "source": "[WHO-Rec3]",
        "difficulty": "easy"
    },
    {
        "question": "Apa saja 8 kelompok makanan kunci yang digunakan WHO dalam pemodelan pola makan bayi 6-23 bulan?",
        "ground_truth": "Kedelapan kelompok makanan kunci WHO/UNICEF adalah: ASI, makanan hewani (daging, ikan, unggas, jeroan), produk susu, telur, kacang-kacangan dan legum, buah/sayur kaya vitamin A, buah/sayur lainnya, serta biji-bijian/umbi-umbian/kentang.",
        "source": "[WHO-Rec4-Background]",
        "difficulty": "easy"
    },
    {
        "question": "Apakah bayi usia 6-23 bulan boleh mengonsumsi minuman manis (sugar-sweetened beverages) menurut WHO?",
        "ground_truth": "Tidak. WHO merekomendasikan secara kuat bahwa minuman manis tidak boleh dikonsumsi oleh bayi dan anak usia 6-23 bulan, meskipun tingkat kepastian buktinya rendah.",
        "source": "[WHO-Rec5b]",
        "difficulty": "easy"
    },
    {
        "question": "Apa perbedaan rekomendasi WHO mengenai jenis susu untuk bayi 6-11 bulan dibandingkan anak 12-23 bulan yang tidak mendapat ASI?",
        "ground_truth": "Untuk bayi 6-11 bulan, WHO menyatakan susu formula maupun susu hewani sama-sama boleh diberikan (rekomendasi kondisional). Untuk anak 12-23 bulan, susu hewani lebih dianjurkan dan susu formula lanjutan (follow-up formula) tidak direkomendasikan, karena di usia ini anak sudah bisa memenuhi kebutuhan gizi dari makanan padat yang lebih beragam.",
        "source": "[WHO-Rec2a] + [WHO-Rec2b]",
        "difficulty": "medium"
    },
    {
        "question": "Mengapa rekomendasi WHO untuk kacang-kacangan/biji-bijian bersifat kondisional, berbeda dengan rekomendasi protein hewani yang bersifat kuat?",
        "ground_truth": "Rekomendasi protein hewani bersifat kuat karena pemodelan diet menunjukkan sumber ini penting untuk menutup kesenjangan zat besi, zinc, dan B12. Sementara rekomendasi kacang-kacangan/biji-bijian hanya kondisional karena buktinya sangat terbatas (very low certainty) dan pemodelan diet menunjukkan mengecualikan kelompok ini hanya berdampak kecil karena bisa dikompensasi kelompok makanan lain — namun tetap penting terutama saat protein hewani sulit didapat.",
        "source": "[WHO-Rec4c]",
        "difficulty": "medium"
    },
    {
        "question": "Apa itu responsive feeding menurut WHO, dan mengapa tetap direkomendasikan secara kuat meskipun bukti pendukungnya bercampur?",
        "ground_truth": "Responsive feeding adalah praktik memberi makan yang mendorong anak makan secara mandiri dan merespons sinyal fisiologis serta perkembangannya, membantu regulasi diri dalam makan. Meskipun hasil studi bervariasi karena perbedaan jenis intervensi yang diteliti, WHO tetap merekomendasikannya secara kuat karena dianggap komponen penting nurturing care yang membantu mencegah kekurangan maupun kelebihan gizi sekaligus mendukung perkembangan anak.",
        "source": "[WHO-Rec7]",
        "difficulty": "medium"
    },

    # ── BUKU KIA 2024 (5: 3 easy, 2 medium) ─────────────────────────

    {
        "question": "Berapa porsi dan frekuensi makan MPASI untuk bayi usia 6-8 bulan menurut Buku KIA 2024?",
        "ground_truth": "Untuk bayi usia 6-8 bulan, porsi dimulai 2-3 sdm bertahap hingga setengah mangkok ukuran 250 ml (125 ml), dengan frekuensi 2-3 kali makanan utama ditambah 1-2 kali makanan selingan per hari.",
        "source": "[KIA-Tabel]",
        "difficulty": "easy"
    },
    {
        "question": "Berapa persen kontribusi ASI dan MPASI terhadap kebutuhan gizi anak usia 12-24 bulan menurut Buku KIA 2024?",
        "ground_truth": "Pada usia 12-24 bulan, sekitar 70% kebutuhan gizi anak dipenuhi dari MPASI, sementara ASI masih menyumbang 30% kebutuhan gizi anak.",
        "source": "[KIA-12-24bln]",
        "difficulty": "easy"
    },
    {
        "question": "Apa saja 4 prinsip utama pemberian MPASI menurut Buku KIA 2024?",
        "ground_truth": "Empat prinsip utama pemberian MPASI adalah: tepat waktu (diberikan mulai usia 6 bulan), cukup sesuai kebutuhan/adekuat (mempertimbangkan jumlah, frekuensi, tekstur, dan variasi), aman (memperhatikan kebersihan makanan dan peralatan), serta diberikan dengan cara yang benar (teratur, lingkungan netral, maksimal 30 menit per sesi makan).",
        "source": "[KIA-Prinsip]",
        "difficulty": "easy"
    },
    {
        "question": "Bagaimana perubahan tekstur dan kebutuhan cairan MPASI dari fase 6-8 bulan hingga 12-23 bulan menurut Buku KIA 2024?",
        "ground_truth": "Tekstur berkembang dari disaring/lumat kental (6-8 bulan), menjadi dicincang (9-11 bulan), hingga masak biasa/diiris seperti makanan keluarga (12-23 bulan). Kebutuhan cairan juga meningkat dari sekitar 800 ml/hari (±3 gelas belimbing) pada usia 6-8 bulan menjadi 1.300 ml/hari (±5 gelas belimbing) pada usia 12-23 bulan.",
        "source": "[KIA-Tabel]",
        "difficulty": "medium"
    },
    {
        "question": "Apa perbedaan cara membuat MPASI dari makanan keluarga matang dibandingkan dari bahan mentah untuk bayi 9-11 bulan?",
        "ground_truth": "Dari makanan keluarga matang: bahan seperti nasi, ikan kembung bumbu kuning, dan tumis buncis langsung dicincang lalu disajikan dengan kuah sayur — lebih praktis. Dari bahan mentah: beras dimasak dulu dengan bumbu tumis (bawang merah, daun salam, kunyit) dan minyak kelapa, baru ikan kembung dan buncis cincang dimasukkan hingga tekstur bubur kasar/cincang tercapai — prosesnya lebih panjang tapi bisa dikontrol penuh dari awal.",
        "source": "[KIA-Cara Buat]",
        "difficulty": "medium"
    },

    # ── INTERVIEW (3: 2 easy, 1 medium) ──────────────────────────────

    {
        "question": "Selain usia dan berat badan, data klinis apa lagi yang perlu diketahui sebelum memberikan rekomendasi MPASI menurut narasumber?",
        "ground_truth": "Data klinis tambahan yang penting meliputi riwayat alergi, riwayat penyakit, jumlah gigi, dan apakah bayi lahir cukup bulan atau tidak. Pada kasus tertentu, bayi yang lahir prematur atau berat badannya tidak bertambah dengan ASI saja mungkin memerlukan MPASI lebih awal dari 6 bulan, dengan syarat kepala sudah bisa tegak.",
        "source": "[I-A1]",
        "difficulty": "easy"
    },
    {
        "question": "Nutrisi apa yang paling sering kurang terpenuhi pada bayi usia 6-24 bulan menurut narasumber, dan apa penyebabnya?",
        "ground_truth": "Nutrisi yang paling sering kurang terpenuhi adalah sayuran dan protein seperti seafood atau telur, yang sulit diberikan karena kekhawatiran orang tua terhadap reaksi alergi. Narasumber menekankan bahwa reaksi alergi yang muncul belum tentu permanen dan bisa dicoba kembali beberapa bulan ke depan.",
        "source": "[I-B2]",
        "difficulty": "easy"
    },
    {
        "question": "Apa dua pola kesalahan paling umum orang tua dalam pemberian tekstur MPASI menurut pengamatan narasumber di lapangan?",
        "ground_truth": "Dua pola kesalahan yang sering ditemui adalah: tekstur dinaikkan terlalu cepat, di mana anak yang seharusnya masih di tekstur lembut/lumat sudah diberi tekstur lebih kasar padahal belum siap; dan sebaliknya, tekstur terlalu lama tidak dinaikkan padahal anak sudah waktunya naik level. Narasumber menilai banyak orang tua kurang peka terhadap kesiapan anaknya.",
        "source": "[I-D1]",
        "difficulty": "medium"
    },

    # ── BUKU RESEP MPASI (3: 2 easy, 1 medium) ───────────────────────

    {
        "question": "Apa saja langkah persiapan yang harus dilakukan sebelum menyiapkan MPASI menurut Buku Resep MPASI Kemenkes?",
        "ground_truth": "Empat langkah persiapan sebelum menyiapkan MPASI adalah: mencuci tangan dengan sabun dan air mengalir, memisahkan makanan mentah dan matang, mencuci serta menyimpan buah dan sayuran mentah di tempat sejuk, dan menyimpan makanan matang dalam wadah tertutup.",
        "source": "[Resep-Persiapan]",
        "difficulty": "easy"
    },
    {
        "question": "Bagaimana komposisi piring MPASI yang dianjurkan untuk bayi usia 6-8 bulan menurut Buku Resep?",
        "ground_truth": "Komposisi piring MPASI usia 6-8 bulan terdiri dari makanan pokok, lauk hewani (diutamakan), lemak dari minyak atau santan, serta sayur dan buah yang ditambahkan.",
        "source": "[Resep-Infografis 6-8bln]",
        "difficulty": "easy"
    },
    {
        "question": "Berikan contoh resep MPASI untuk bayi 9-11 bulan dari Buku Resep beserta bahan utamanya.",
        "ground_truth": "Salah satu contohnya adalah Nasi Tim Ikan Tuna Telur Puyuh, dengan bahan utama nasi putih, ikan tuna segar yang dihaluskan, telur puyuh, wortel, tomat, minyak kelapa, dan kaldu ayam, dimasak dengan cara ditim hingga matang lalu disajikan dengan saus pepaya.",
        "source": "[Resep-9-11bln]",
        "difficulty": "medium"
    },

    # ── CROSS-SOURCE SYNTHESIS (3 hard) ──────────────────────────────

    {
        "question": "Bagaimana seharusnya waktu pemberian MPASI ditentukan untuk bayi prematur, dengan mempertimbangkan panduan usia koreksi dari narasumber dan rekomendasi umum WHO usia 6 bulan?",
        "ground_truth": "WHO merekomendasikan MPASI dimulai pada usia 6 bulan (180 hari) sebagai panduan kesehatan masyarakat umum. Namun untuk bayi prematur, narasumber menjelaskan bahwa usia harus dihitung berdasarkan usia koreksi, bukan usia kronologis — misalnya bayi lahir di usia kehamilan 32 minggu memiliki usia koreksi yang jauh lebih muda dari usia kalendernya. Bayi lahir cukup bulan namun berat rendah (kemungkinan PJT) tetap mengikuti usia kronologis. Keputusan akhir tetap harus berkolaborasi dengan Dokter Spesialis Anak (DSA) untuk kasus prematur ini.",
        "source": "[I-A3] + [WHO-Rec3]",
        "difficulty": "hard"
    },
    {
        "question": "Bagaimana risiko defisiensi zat besi akibat konsumsi susu hewani pada bayi 6-11 bulan (menurut WHO) dapat diimbangi dengan rekomendasi sumber protein dari narasumber dan Buku KIA?",
        "ground_truth": "WHO menemukan bahwa susu hewani pada bayi 6-11 bulan berisiko meningkatkan anemia dan defisiensi zat besi dibandingkan susu formula, meski gap ini bisa diatasi lewat makanan lain, suplemen, atau produk fortifikasi. Sejalan dengan ini, narasumber merekomendasikan 2 butir telur rebus per hari sebagai sumber protein hewani terjangkau untuk mencegah stunting, sementara Buku KIA menekankan protein hewani (ikan, ayam, daging, hati, telur) sebagai prioritas utama dalam variasi MPASI. Kombinasi susu hewani dengan sumber protein hewani padat zat besi lainnya dapat membantu menutup kesenjangan gizi tersebut.",
        "source": "[WHO-Rec2a] + [I-D2] + [KIA-Variasi]",
        "difficulty": "hard"
    },
    {
        "question": "Jika bayi 9-11 bulan diduga alergi telur, bagaimana seharusnya menu MPASI-nya disusun dengan mempertimbangkan rekomendasi protein hewani harian WHO, tabel porsi Buku KIA, serta catatan narasumber tentang alergi protein?",
        "ground_truth": "WHO merekomendasikan secara kuat bahwa protein hewani (daging, ikan, atau telur) dikonsumsi setiap hari, dengan porsi bayi 9-11 bulan sekitar setengah hingga tiga perempat mangkok per kali makan menurut Buku KIA. Namun narasumber mencatat bahwa telur dan seafood adalah sumber protein yang paling sering memicu alergi pada bayi, meski reaksi tersebut belum tentu permanen dan bisa dicoba ulang beberapa bulan kemudian. Untuk bayi dengan dugaan alergi telur, menu tetap harus memenuhi kebutuhan protein hewani harian dengan mengganti sumber lain seperti ikan, ayam, atau daging cincang, sambil berkonsultasi dengan tenaga kesehatan mengenai kapan dan bagaimana telur bisa dicoba kembali secara bertahap.",
        "source": "[WHO-Rec4a] + [KIA-Tabel] + [I-B2]",
        "difficulty": "hard"
    },

]

def build_dataset() -> list:
    dataset = []
    total = len(RAW_QUESTIONS)

    for i, item in enumerate(RAW_QUESTIONS):
        print(f"[{i+1}/{total}] {item['question'][:60]}...")
        try:
            result = answer_question(item["question"])
            dataset.append({
                "question": result["question"],
                "answer": result["answer"],
                "contexts": result["contexts"],
                "ground_truth": item["ground_truth"],
                "difficulty": item["difficulty"],  # ADDED: biar ke-carry sampe json output, buat analisis per-tier nanti
                "source": item["source"],  # ADDED: sekalian, biar gampang trace balik pas cek hasil
            })
            print(f"  -> OK, {len(result['contexts'])} chunks retrieved")
        except Exception as e:
            print(f"  -> GAGAL: {e}")
            dataset.append({
                "question": item["question"],
                "answer": "",
                "contexts": [],
                "ground_truth": item["ground_truth"],
                "difficulty": item["difficulty"],  # ADDED: sama, biar konsisten walau gagal
                "source": item["source"],  # ADDED
                "error": str(e),
            })

    return dataset

if __name__ == "__main__":
    print("Membangun RAGAS dataset...\n")
    dataset = build_dataset()

    output_path = "eval_dataset_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\nSelesai. {len(dataset)} entri disimpan ke {output_path}")