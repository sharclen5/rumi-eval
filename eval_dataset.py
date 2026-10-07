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

# REBUILT: 20 pertanyaan baru — dirancang sesuai fungsi nyata sistem
# (generate meal plan berdasarkan data bayi + KB chunks)
# Ground truth 100% dijangkar ke konten KB aktual
# Distribusi: 10 easy / 7 medium / 3 hard
RAW_QUESTIONS = [

    # ── EASY (10) ────────────────────────────────────────────────────

    {
        "question": "Pada usia berapa bayi sebaiknya mulai diberikan MPASI menurut WHO?",
        "ground_truth": "Menurut WHO, bayi sebaiknya mulai diperkenalkan dengan makanan pendamping ASI (MPASI) pada usia 6 bulan sambil tetap melanjutkan pemberian ASI.",
        "source": "[WHO-Rec3]",
        "difficulty": "easy",
    },
    {
        "question": "Apa tekstur MPASI yang tepat untuk bayi usia 9-11 bulan menurut Buku KIA 2024?",
        "ground_truth": "Untuk bayi usia 9-11 bulan, tekstur MPASI yang dianjurkan adalah dicincang — bahan makanannya sama dengan makanan orang dewasa, namun dicincang terlebih dahulu sebelum disajikan kepada bayi.",
        "source": "[KIA-Tabel]",
        "difficulty": "easy",
    },
    {
        "question": "Berapa porsi dan frekuensi makan MPASI untuk bayi usia 6-8 bulan menurut Buku KIA 2024?",
        "ground_truth": "Untuk bayi usia 6-8 bulan, porsi dimulai dari 2-3 sendok makan dan ditingkatkan bertahap hingga setengah mangkok ukuran 250 ml (sekitar 125 ml). Frekuensinya adalah 2-3 kali makanan utama ditambah 1-2 kali makanan selingan per hari.",
        "source": "[KIA-Tabel]",
        "difficulty": "easy",
    },
    {
        "question": "Apakah bayi usia 6-23 bulan boleh diberikan minuman manis atau sugar-sweetened beverages menurut WHO?",
        "ground_truth": "Tidak. WHO merekomendasikan secara kuat bahwa minuman manis (sugar-sweetened beverages) tidak boleh dikonsumsi oleh bayi dan anak usia 6-23 bulan, meskipun tingkat kepastian buktinya rendah.",
        "source": "[WHO-Rec5b]",
        "difficulty": "easy",
    },
    {
        "question": "Apa saja sumber protein hewani yang bisa digunakan dalam MPASI bayi menurut Buku KIA 2024?",
        "ground_truth": "Menurut Buku KIA 2024, sumber protein hewani yang bisa digunakan dalam MPASI antara lain ikan, ayam, daging, hati, udang, telur, susu dan hasil olahannya. Pemberian protein hewani dalam MPASI diprioritaskan.",
        "source": "[KIA-Variasi]",
        "difficulty": "easy",
    },
    {
        "question": "Bahan makanan apa saja yang termasuk sumber karbohidrat untuk MPASI bayi menurut Buku KIA 2024?",
        "ground_truth": "Menurut Buku KIA 2024, sumber karbohidrat (makanan pokok) untuk MPASI meliputi beras, biji-bijian, jagung, gandum, sagu, umbi, kentang, singkong, dan lain-lain.",
        "source": "[KIA-Variasi]",
        "difficulty": "easy",
    },
    {
        "question": "Selain usia dan berat badan, data klinis apa lagi yang penting diketahui sebelum memberikan rekomendasi MPASI menurut narasumber?",
        "ground_truth": "Menurut narasumber, data klinis tambahan yang penting meliputi riwayat alergi, riwayat penyakit, jumlah gigi, dan apakah bayi lahir cukup bulan atau tidak. Pada kasus tertentu, bayi yang lahir prematur atau berat badannya tidak bertambah optimal dengan ASI saja mungkin memerlukan MPASI lebih awal dari 6 bulan, dengan syarat kepala sudah bisa tegak.",
        "source": "[I-A1]",
        "difficulty": "easy",
    },
    {
        "question": "Apa saja langkah persiapan yang harus dilakukan sebelum menyiapkan MPASI menurut Buku Resep MPASI Kemenkes?",
        "ground_truth": "Empat langkah persiapan sebelum menyiapkan MPASI adalah: mencuci tangan dengan sabun dan air mengalir, memisahkan makanan mentah dan matang, mencuci serta menyimpan buah dan sayuran mentah di tempat sejuk, dan menyimpan makanan matang dalam wadah tertutup.",
        "source": "[Resep-Persiapan]",
        "difficulty": "easy",
    },
    {
        "question": "Apa contoh resep MPASI untuk bayi 9-12 bulan dari Buku KIA 2024 beserta bahan utamanya?",
        "ground_truth": "Buku KIA 2024 menyediakan resep Nasi Tim Ikan Kembung Telur Puyuh untuk bayi usia 9-12 bulan. Bahan utamanya meliputi nasi putih, ikan kembung segar yang dihaluskan, telur puyuh, wortel, tomat, minyak kelapa, dan kaldu ayam. Cara membuatnya: semua bahan dimasukkan ke mangkok tim, ditambahkan kaldu, lalu ditim hingga matang dan disajikan dengan saus pepaya yang dihaluskan.",
        "source": "[KIA-Resep9-12bln]",
        "difficulty": "easy",
    },
    {
        "question": "Nutrisi apa yang paling sering kurang terpenuhi pada bayi usia 6-24 bulan menurut narasumber, dan apa penyebabnya?",
        "ground_truth": "Menurut narasumber, nutrisi yang paling sering kurang terpenuhi adalah sayuran dan protein seperti seafood atau telur, yang sulit diberikan karena kekhawatiran orang tua terhadap reaksi alergi. Narasumber menekankan bahwa reaksi alergi yang muncul belum tentu permanen dan bisa dicoba kembali beberapa bulan ke depan.",
        "source": "[I-B2]",
        "difficulty": "easy",
    },

    # ── MEDIUM (7) ───────────────────────────────────────────────────

    {
        "question": "Bagaimana tekstur MPASI harus disesuaikan ketika bayi berusia 8 bulan dan mulai tumbuh gigi menurut narasumber?",
        "ground_truth": "Menurut narasumber, untuk bayi usia 6-8 bulan tekstur yang diberikan adalah lumat. Namun memasuki bulan ke-8, tekstur bisa mulai dinaikkan sedikit — hal ini bisa dilihat dari tumbuh gigi sebagai sinyal kesiapan bayi untuk menerima tekstur yang lebih kasar. Orang tua perlu peka terhadap kesiapan anaknya dalam merespons perubahan tekstur ini.",
        "source": "[I-B3]",
        "difficulty": "medium",
    },
    {
        "question": "Bagaimana porsi MPASI bisa ditambah dan kapan penambahan porsi itu dianjurkan menurut narasumber?",
        "ground_truth": "Menurut narasumber, penambahan porsi bisa dilakukan jika porsi 80 ml sudah habis dalam waktu kurang dari 30 menit. Penambahan ini terutama dianjurkan di awal-awal masa MPASI, karena seiring berjalannya waktu biasanya anak justru semakin sulit makan.",
        "source": "[I-A2]",
        "difficulty": "medium",
    },
    {
        "question": "Makanan dan minuman apa saja yang harus dihindari untuk anak usia 12-24 bulan menurut Buku KIA 2024?",
        "ground_truth": "Menurut Buku KIA 2024, untuk anak usia 12-24 bulan harus dihindari: susu atau yoghurt rendah lemak, minuman bersoda, makanan yang terlalu asam dan pedas, makanan dan minuman yang tinggi kandungan gula atau menggunakan pemanis buatan seperti minuman kemasan dan kalengan, serta makanan yang banyak mengandung MSG dan bahan pengawet seperti makanan instan.",
        "source": "[KIA-12-24bln]",
        "difficulty": "medium",
    },
    {
        "question": "Apa dua pola kesalahan paling umum orang tua dalam pemberian tekstur MPASI menurut narasumber?",
        "ground_truth": "Dua pola kesalahan yang sering ditemui narasumber di lapangan adalah: pertama, tekstur dinaikkan terlalu cepat — anak yang seharusnya masih di tekstur lembut/lumat sudah diberi tekstur lebih kasar padahal belum siap; kedua, tekstur terlalu lama tidak dinaikkan padahal anak sudah waktunya naik level. Narasumber menilai banyak orang tua kurang peka terhadap kesiapan anaknya.",
        "source": "[I-D1]",
        "difficulty": "medium",
    },
    {
        "question": "Kondisi apa saja yang membuat sistem rekomendasi MPASI harus merujuk orang tua langsung ke tenaga kesehatan menurut narasumber?",
        "ground_truth": "Menurut narasumber, sistem sebaiknya merujuk langsung ke tenaga kesehatan bila ditemukan: tanda bahaya seperti demam tinggi, diare atau muntah berulang, sesak napas, atau kejang; berat badan tidak naik atau gagal tumbuh; reaksi alergi berat; bayi prematur atau BBLR yang memerlukan usia koreksi; GTM berkepanjangan; serta kondisi disabilitas atau komorbid.",
        "source": "[I-C2]",
        "difficulty": "medium",
    },
    {
        "question": "Apa saja rekomendasi pencegahan stunting yang bisa diterapkan pada kondisi sosial-ekonomi terbatas menurut narasumber?",
        "ground_truth": "Menurut narasumber, salah satu rekomendasi praktis untuk kondisi sosial-ekonomi terbatas adalah menyelingi MPASI dengan 2 butir telur rebus per hari sebagai sumber protein hewani yang terjangkau untuk mencegah stunting.",
        "source": "[I-D2]",
        "difficulty": "medium",
    },
    {
        "question": "Apa perbedaan cara membuat MPASI dari makanan keluarga yang sudah matang dibandingkan dari bahan mentah untuk bayi 9-11 bulan menurut Buku KIA 2024?",
        "ground_truth": "Menurut Buku KIA 2024, untuk bayi 9-11 bulan: dari makanan keluarga matang — nasi, ikan kembung bumbu kuning, dan tumis buncis dicincang lalu disajikan dengan kuah sayur (santan kare). Dari bahan mentah — beras dimasak dengan bumbu yang telah ditumis (bawang merah, daun salam, kunyit) dan minyak kelapa, kemudian ikan kembung dan buncis yang telah dicincang dimasukkan dan diaduk hingga mendapatkan konsistensi bubur kasar/cincang.",
        "source": "[KIA-CaraBuat]",
        "difficulty": "medium",
    },

    # ── HARD (3) — cross-source synthesis ───────────────────────────

    {
        "question": "Bagaimana menentukan waktu mulai MPASI untuk bayi prematur, dengan mempertimbangkan rekomendasi umum usia 6 bulan dari WHO dan panduan usia koreksi dari narasumber?",
        "ground_truth": "WHO merekomendasikan MPASI dimulai pada usia 6 bulan (180 hari) sebagai panduan umum sambil tetap melanjutkan ASI. Namun untuk bayi prematur, narasumber menjelaskan bahwa waktu MPASI harus dihitung berdasarkan usia koreksi, bukan usia kronologis — misalnya bayi lahir di usia kehamilan 32 minggu memiliki usia koreksi yang jauh lebih muda dari usia kalendernya. Pengecualian berlaku jika bayi lahir cukup bulan (37-40 minggu) namun berat badan rendah (kemungkinan PJT), maka MPASI tetap mengikuti usia kronologis. Keputusan akhir tetap harus berkolaborasi dengan Dokter Spesialis Anak (DSA).",
        "source": "[WHO-Rec3] + [I-A3]",
        "difficulty": "hard",
    },
    {
        "question": "Jika bayi usia 9-11 bulan diduga alergi telur, bagaimana menyusun menu MPASI yang tetap memenuhi kebutuhan protein hewani harian menurut WHO dan porsi yang sesuai menurut Buku KIA 2024, dengan mempertimbangkan catatan narasumber tentang alergi?",
        "ground_truth": "WHO merekomendasikan secara kuat bahwa protein hewani seperti daging, ikan, atau telur dikonsumsi setiap hari oleh bayi usia 6-23 bulan. Untuk bayi 9-11 bulan, Buku KIA 2024 menetapkan porsi setengah hingga tiga perempat mangkok ukuran 250 ml per kali makan. Narasumber mencatat bahwa telur dan seafood adalah protein yang paling sering memicu alergi, namun reaksi tersebut belum tentu permanen dan bisa dicoba ulang beberapa bulan kemudian. Untuk bayi dengan dugaan alergi telur, kebutuhan protein hewani harian tetap harus dipenuhi dengan mengganti sumber lain seperti ikan, ayam, atau daging cincang sesuai porsi yang dianjurkan, sambil berkonsultasi dengan tenaga kesehatan mengenai kapan telur bisa dicoba kembali.",
        "source": "[WHO-Rec4a] + [KIA-Tabel] + [I-B2]",
        "difficulty": "hard",
    },
    {
        "question": "Bagaimana panduan Buku KIA 2024 dan rekomendasi narasumber dapat saling melengkapi dalam menyusun MPASI untuk bayi usia 6-8 bulan dari bahan lokal yang terjangkau?",
        "ground_truth": "Buku KIA 2024 menyediakan contoh bahan lokal untuk bayi 6-8 bulan dari bahan mentah: beras putih, telur ayam, tempe kedelai, wortel, dan santan — dimasak dengan bumbu tumis (bawang merah, daun salam, kunyit) hingga konsistensi bubur kental. Tekstur pada usia ini harus disaring/lumat dan kental, dengan porsi 2-3 sdm bertahap hingga setengah mangkok, 2-3 kali makanan utama per hari. Narasumber melengkapi dengan rekomendasi bahwa untuk kondisi ekonomi terbatas, 2 butir telur rebus per hari bisa dijadikan sumber protein hewani terjangkau untuk mencegah stunting, dan mengingatkan bahwa menu sebaiknya sudah mencakup protein hewani, nabati, dan sayuran dalam satu hari (menu 4-5 bintang), bukan menu tunggal.",
        "source": "[KIA-CaraBuat] + [KIA-Tabel] + [I-D2] + [I-B1]",
        "difficulty": "hard",
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