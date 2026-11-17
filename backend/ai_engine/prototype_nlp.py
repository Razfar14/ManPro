"""
Prototype AI Engine (Behind The Headline)
Mesin analisis NLP berbasis konten aktual artikel:
1. Selalu merangkum topik berdasarkan artikel nyata yang ditemukan (tidak mengarang topik/media lain).
2. Menyelaraskan nama media di ringkasan, tabel perbandingan, dan daftar berita asli.
3. Mengekstrak fakta/angka, tokoh/lembaga/narasumber, dan fokus unik per artikel tanpa template generik.
4. Menolak topik nyeleneh/tidak valid dengan pesan penolakan standar.
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from backend.ai_engine.base import BaseAIEngine
from backend.ai_engine.topic_validator import (
    ABSURD_TOPIC_MESSAGE,
    is_absurd_or_invalid_topic,
)

logger = logging.getLogger("PrototypeAIEngine")

# Lembaga, organisasi, dan entitas berita Indonesia yang sering menjadi subjek/narasumber
KNOWN_INSTITUTIONS = [
    "PP Muhammadiyah", "Muhammadiyah", "PBNU", "NU", "KPK", "KPU", "Bawaslu",
    "DPR RI", "DPR", "MPR", "DPD", "MK", "MA", "Kejaksaan Agung", "Kejagung",
    "Polri", "TNI", "Kemenkeu", "Kementerian Keuangan", "Kemendikbud", "Kemenkes",
    "Komdigi", "Kemenkomdigi", "Kominfo", "BMKG", "Bank Indonesia", "BI", "OJK",
    "LPS", "BPJS", "Bappenas", "Walhi", "Celios", "Aprindo", "KSPI", "Kadin",
    "Golkar", "PDIP", "PDI-P", "Gerindra", "PKB", "PKS", "NasDem", "PAN", "PSI",
    "Demokrat", "PPP", "Transparency International", "ICW", "YLBHI", "Komnas HAM",
    "Pemprov DKI", "Kementerian PU", "Ditjen Pajak", "Istana", "Pemerintah"
]

# Tokoh publik yang sering muncul di berita Indonesia tanpa gelar di depan namanya
KNOWN_FIGURES = [
    "Prabowo Subianto", "Prabowo", "Gibran Rakabuming Raka", "Gibran",
    "Joko Widodo", "Jokowi", "Sri Mulyani Indrawati", "Sri Mulyani",
    "Haedar Nashir", "Abdul Mu'ti", "Anies Baswedan", "Ganjar Pranowo",
    "Bahlil Lahadalia", "Airlangga Hartarto", "Muhaimin Iskandar", "Cak Imin",
    "Agus Harimurti Yudhoyono", "AHY", "Puan Maharani", "Surya Paloh",
    "Megawati Soekarnoputri", "Megawati", "Mahfud MD", "Luhut Binsar Pandjaitan",
    "Erick Thohir", "Sufmi Dasco Ahmad", "Dasco", "Ahmad Muzani",
    "Pramono Anung", "Ridwan Kamil", "Dedi Mulyadi", "Khofifah Indar Parawansa",
    "Bhima Yudhistira", "Said Iqbal", "Roy Nicholas Mandey", "Purbaya Yudhi Sadewa"
]

# Kata-kata yang tidak boleh dianggap sebagai nama orang
NON_PERSON_CAPITALIZED = {
    "Jakarta", "Indonesia", "Yogyakarta", "Bandung", "Surabaya", "Semarang", "Medan",
    "Makassar", "Bali", "Papua", "Aceh", "Nasional", "Politik", "Ekonomi", "Hukum",
    "Teknologi", "Lingkungan", "Berita", "Laporan", "Pemerintah", "Presiden", "Wakil",
    "Menteri", "Ketua", "Direktur", "Kepala", "Pengamat", "Pakar", "Dinamika",
    "Bursa", "Calon", "Pengganti", "Pesan", "Kebangsaan", "Sorotan", "Wacana",
    "Isu", "Kasus", "Dugaan", "Rencana", "Kenaikan", "Tarif", "Harga", "Update",
    "Terbaru", "Terkini", "Hari", "Ini", "Senin", "Selasa", "Rabu", "Kamis",
    "Jumat", "Sabtu", "Minggu", "Januari", "Februari", "Maret", "April", "Mei",
    "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    "Persen", "Berlaku", "Mulai", "Menghangat", "Menjelang", "Tengah", "Kinerja",
    "Ekspor", "Impor", "Naik", "Turun", "Bertabur", "Makian", "Ancaman",
    "Soroti", "Nilai", "Sebut", "Ungkap", "Tegas", "Ujar", "Jelaskan", "Bahas",
    "Kritik", "Dorong", "Tuntut", "Pantau", "Petakan", "Siapkan", "Pastikan", "Sita",
    "ANTARA", "News", "Detik", "DetikNews", "Tempo", "CNN", "CNBC", "Kompas",
    "Aktual", "Republika", "Liputan6", "Kumparan", "Tribun", "Sindo", "Okezone",
    "Namun", "Sementara", "Selain", "Menurut", "Dalam", "Untuk", "Pada", "Dari",
    "Oleh", "Dengan", "Setelah", "Sebelum", "Saat", "Terkait", "Soal", "Jika"
}

STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "pada", "dalam", "untuk", "dengan", "atau",
    "itu", "ini", "akan", "telah", "sudah", "bisa", "dapat", "juga", "serta", "oleh",
    "saat", "tentang", "terkait", "soal", "atas", "bagi", "sebagai", "karena", "agar",
    "namun", "tetapi", "sedangkan", "sementara", "melalui", "menjadi", "antara",
    "sebuah", "para", "tersebut", "hingga", "sampai", "lebih", "kurang", "masih",
    "bahwa", "usai", "pasca", "jelang", "berita", "terbaru", "hari", "indonesia"
}


class PrototypeAIEngine(BaseAIEngine):
    """
    Mesin AI Prototype berbasis ekstraksi fakta dan sintesis konten aktual artikel.
    """

    def _clean_lead_text(self, text: str) -> str:
        cleaned = re.sub(r"^[A-Z][a-zA-Z\s\.]+,\s*[A-Za-z0-9\.\s]+--\s*", "", (text or "").strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _clean_title(self, title: str, publisher: str = "") -> str:
        t = (title or "").strip()
        if publisher:
            t = re.sub(rf"\s*[-–|]\s*{re.escape(publisher)}\s*$", "", t, flags=re.IGNORECASE).strip()
        return re.sub(r"\s+", " ", t).strip()

    def _is_duplicate_snippet(self, title: str, snippet: str, publisher: str = "") -> bool:
        if not snippet:
            return True
        s_low = re.sub(r"\W+", " ", snippet.lower()).strip()
        t_low = re.sub(r"\W+", " ", self._clean_title(title, publisher).lower()).strip()
        if not s_low or len(s_low) < 25:
            return True
        if s_low == t_low or s_low.startswith(t_low) and len(s_low) <= len(t_low) + len(publisher) + 12:
            return True
        return False

    def _get_meaningful_body(self, art: Dict[str, Any]) -> str:
        """Mengambil isi bermakna dari artikel (full_text jika ada, atau snippet non-duplikat)."""
        title = art.get("title", "")
        publisher = art.get("publisher", "")
        full_text = self._clean_lead_text(art.get("full_text", ""))
        snippet = self._clean_lead_text(art.get("snippet", ""))

        if full_text and not self._is_duplicate_snippet(title, full_text, publisher):
            return full_text
        if snippet and not self._is_duplicate_snippet(title, snippet, publisher):
            return snippet
        return ""

    def _extract_figures(self, text: str) -> List[str]:
        patterns = [
            r"Rp\s?[\d\.,]+(?:\s?(?:triliun|miliar|juta|ribu))?",
            r"US\$\s?[\d\.,]+(?:\s?(?:miliar|juta|ribu|billion|million))?",
            r"[\d\.,]+\s?%",
            r"[\d\.,]+\s?(?:persen|triliun|miliar|juta|ribu|kilometer|km|jam|orang|daerah|kabupaten|kota|provinsi|kursi|suara|tahun|periode|pasal|ayat)",
            r"\b(?:202[0-9]|203[0-5])\b",
            r"\b(?:Pasal|UU Nomor|UU No\.?)\s+[\d\w/\.]+"
        ]
        found = []
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                clean_m = re.sub(r"\s+", " ", m).strip()
                if clean_m and clean_m not in found and len(clean_m) > 1:
                    found.append(clean_m)
        return found[:4]

    def _extract_sources(self, text: str, title: str = "") -> List[str]:
        """
        Mengekstrak nama tokoh, pejabat, lembaga/organisasi, atau pihak kunci
        yang dikutip atau menjadi aktor utama dalam artikel tanpa false-positive Title Case.
        """
        combined = f"{title}. {text}".strip()
        sources: List[str] = []

        def _add_source(val: str):
            clean = re.sub(r"\s+", " ", val).strip(" ,.;:")
            if not clean or len(clean) < 2:
                return
            for existing in sources:
                if clean.lower() == existing.lower() or clean.lower() in existing.lower():
                    return
            sources.append(clean)

        # 1. Tokoh publik dikenal (urut terpanjang dulu agar nama lengkap diprioritaskan)
        for fig in sorted(KNOWN_FIGURES, key=len, reverse=True):
            if re.search(rf"\b{re.escape(fig)}\b", combined):
                _add_source(fig)

        # 2. Lembaga / organisasi dikenal
        for inst in sorted(KNOWN_INSTITUTIONS, key=len, reverse=True):
            if re.search(rf"\b{re.escape(inst)}\b", combined):
                _add_source(inst)

        # 3. Pejabat / profesi + nama orang (misal: Menteri Keuangan Sri Mulyani)
        role_person_pat = (
            r"(?:Menteri Keuangan|Menteri Dalam Negeri|Menteri Luar Negeri|Menteri Hukum|Menteri|"
            r"Menkeu|Menko|Ketua Umum|Ketum|Wakil Ketua|Ketua|Sekjen|"
            r"Direktur Eksekutif|Direktur Utama|Direktur|Kepala|"
            r"Pakar|Pengamat|Peneliti|Guru Besar|Rektor|Gubernur|Bupati|Wali Kota|"
            r"Juru Bicara|Jubir)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
        )
        for m in re.finditer(role_person_pat, combined):
            candidate = m.group(0).strip(" ,.;:")
            tail_words = m.group(1).split()
            if not any(w in NON_PERSON_CAPITALIZED for w in tail_words):
                _add_source(candidate)

        # 4. Kutipan langsung di isi kalimat ("kata/ujar/menurut <Tokoh>")
        quote_pat = r"(?:ujar|kata|tegas|menurut|tutur|ungkap|nilai|sorot|sebut|jelas|imbau)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
        for m in re.finditer(quote_pat, text or ""):
            name = m.group(1).strip(" ,.;:")
            parts = name.split()
            if not any(p in NON_PERSON_CAPITALIZED for p in parts):
                _add_source(name)

        # 5. Peran eksplisit jika belum terambil (misal "Pengamat Politik", "Pengusaha Ritel", "Serikat Buruh")
        for role_kw in ["Pengamat Politik", "Pengamat Ekonomi", "Ekonom", "Serikat Buruh", "Pelaku Usaha", "Pengusaha Ritel", "Warga"]:
            if re.search(rf"\b{re.escape(role_kw)}\b", combined, re.IGNORECASE):
                _add_source(role_kw)

        return sources[:3]

    def _extract_article_focus(self, art: Dict[str, Any]) -> str:
        """
        Menyusun ringkasan fokus spesifik satu artikel berdasarkan judul dan paragraf pembukanya.
        """
        title = self._clean_title(art.get("title", ""), art.get("publisher", ""))
        body = self._get_meaningful_body(art)

        if body:
            # Ambil kalimat pertama/kedua yang informatif dari isi artikel
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.strip()) > 30]
            for sent in sentences:
                if title.lower()[:25] not in sent.lower():
                    return sent[:190].rstrip(" ,;:") + ("..." if len(sent) > 190 else "")
            if sentences:
                return sentences[0][:190].rstrip(" ,;:") + ("..." if len(sentences[0]) > 190 else "")

        if title:
            return title
        return "Pemberitaan terkait topik pencarian"

    def _extract_common_themes(self, query: str, articles: List[Dict[str, Any]]) -> List[str]:
        """Mengekstrak frasa/kata kunci dominan dari kumpulan judul & isi artikel."""
        freq: Dict[str, int] = {}
        q_tokens = set(re.findall(r"[a-z]+", query.lower()))

        for art in articles:
            title = self._clean_title(art.get("title", ""), art.get("publisher", ""))
            body = self._get_meaningful_body(art)[:400]
            words = re.findall(r"[A-Za-zÀ-ÿ0-9\-]{3,}", f"{title} {body}")
            seen_in_art = set()
            for w in words:
                wl = w.lower()
                if wl in STOPWORDS_ID or wl in q_tokens or wl.isdigit():
                    continue
                if wl not in seen_in_art:
                    seen_in_art.add(wl)
                    freq[w] = freq.get(w, 0) + (2 if w[0].isupper() else 1)

        ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        themes = []
        seen_low = set()
        for word, _ in ranked:
            if word.lower() not in seen_low:
                seen_low.add(word.lower())
                themes.append(word)
            if len(themes) >= 6:
                break
        return themes

    def _select_comparison_articles(self, articles: List[Dict[str, Any]], max_slots: int = 3) -> List[Dict[str, Any]]:
        """Memilih hingga 3 artikel dengan prioritas penerbit berbeda agar perbandingan antarmedia seimbang."""
        selected: List[Dict[str, Any]] = []
        used_publishers = set()
        leftovers: List[Dict[str, Any]] = []

        for art in articles:
            pub = (art.get("publisher") or "Media Daring").strip()
            pub_low = pub.lower()
            if pub_low not in used_publishers and len(selected) < max_slots:
                used_publishers.add(pub_low)
                selected.append(art)
            else:
                leftovers.append(art)

        while len(selected) < max_slots and leftovers:
            selected.append(leftovers.pop(0))

        return selected

    def summarize_topic(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan topik berita secara tematik, klasifikasi,
        serta penjelasan konteks substansi topik yang dibahas berdasarkan isi artikel.
        """
        title = self._clean_title(article.get("title", ""), article.get("publisher", ""))
        publisher = (article.get("publisher", "Media Daring") or "Media Daring").strip()
        category = (article.get("category", "Nasional") or "Nasional").strip()
        body = self._get_meaningful_body(article)
        combined = f"{title} {body} {category}".lower()

        if any(k in combined for k in ["ekspor", "impor", "perdagangan", "ppn", "pajak", "rupiah", "ihsg", "inflasi", "saham", "ritel", "devisa", "komoditas", "fiskal", "apbn", "bank", "ekonomi"]):
            subtopik = "Ekonomi & Perdagangan"
            alasan = "membahas aktivitas perdagangan komoditas, kebijakan fiskal/perpajakan, atau dinamika pasar yang berdampak pada stabilitas perekonomian nasional"
            dampak = "Pemahaman atas topik ini membantu pembaca melihat keterkaitan antara kebijakan ekonomi, pelaku usaha, dan daya beli masyarakat."
        elif any(k in combined for k in ["pidato", "prabowo", "gibran", "jokowi", "presiden", "wapres", "cawapres", "menteri", "dpr", "kpu", "pilkada", "pemilu", "partai", "koalisi", "oposisi", "gerindra", "politik", "kebijakan pemerintah", "kebangsaan"]):
            subtopik = "Politik & Tata Kelola Pemerintahan"
            alasan = "menyoroti dinamika kepemimpinan nasional, bursa figur politik, pesan kebangsaan, atau pengambilan keputusan di ranah pemerintahan"
            dampak = "Isu ini penting dicermati untuk memahami arah koalisi, dinamika elite politik, serta implikasinya terhadap stabilitas pemerintahan."
        elif any(k in combined for k in ["hukum", "kpk", "polisi", "kejaksaan", "tersangka", "sidang", "korupsi", "hakim", "vonis", "kasus", "penyidik", "perampasan aset", "uu "]):
            subtopik = "Hukum & Penegakan Keadilan"
            alasan = "mengulas proses penyidikan, peradilan perkara tindak pidana, serta upaya penguatan regulasi dan pemberantasan korupsi"
            dampak = "Perkembangan isu ini berpengaruh langsung pada kepastian hukum dan integritas lembaga penegak hukum."
        elif any(k in combined for k in ["ai", "kecerdasan buatan", "teknologi", "digital", "siber", "data center", "gadget", "aplikasi", "kominfo", "komdigi", "internet"]):
            subtopik = "Teknologi & Transformasi Digital"
            alasan = "mengulas perkembangan inovasi komputasi modern, infrastruktur pusat data, serta tata kelola ekosistem digital"
            dampak = "Topik ini krusial karena menyangkut kesiapan sumber daya manusia, perlindungan data, dan daya saing teknologi nasional."
        elif any(k in combined for k in ["banjir", "cuaca", "iklim", "gempa", "hujan", "ciliwung", "lingkungan", "sampah", "polusi", "karhutla", "walhi", "resapan"]):
            subtopik = "Lingkungan & Keberlanjutan Ekologis"
            alasan = "membahas kondisi ekologis, mitigasi risiko bencana, serta tata ruang dan kesiapsiagaan infrastruktur"
            dampak = "Pembahasan topik ini menyoroti keseimbangan antara pembangunan fisik, pelestarian ekosistem, dan keselamatan warga."
        else:
            subtopik = f"{category} & Isu Publik"
            alasan = f"mengangkat dinamika sosial dan kebijakan strategis yang berkaitan dengan sektor {category}"
            dampak = "Topik ini memberi gambaran kontekstual bagi pembaca untuk membandingkan fokus pemberitaan lintas media."

        figures = self._extract_figures(f"{title} {body}")
        sources = self._extract_sources(body, title)
        detail_parts = []
        if title:
            detail_parts.append(f"Secara khusus, laporan {publisher} berjudul \"{title}\" menyoroti inti persoalan ini")
        if sources:
            detail_parts.append(f"dengan melibatkan/mengutip {', '.join(sources[:2])}")
        if figures:
            detail_parts.append(f"serta mencantumkan indikator angka ({', '.join(figures[:2])})")

        detail_sentence = (" ".join(detail_parts) + ".") if detail_parts else ""

        return (
            f"Topik: {subtopik}. "
            f"Berita ini diklasifikasikan ke dalam ranah {subtopik} karena {alasan} berdasarkan pelaporan {publisher}. "
            f"{detail_sentence} {dampak}"
        ).strip()

    def summarize_article(self, article: Dict[str, Any]) -> str:
        title = self._clean_title(article.get("title", ""), article.get("publisher", ""))
        publisher = article.get("publisher", "Media")
        body = self._get_meaningful_body(article)

        if body:
            paras = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 30]
            if len(paras) >= 2:
                return f"{paras[0]} Laporan {publisher} lebih lanjut menyoroti bahwa {paras[1][:220]}"
            return f"Berdasarkan laporan {publisher}, {body[:260]}"

        return f"Artikel {publisher} berjudul '{title}' menyoroti perkembangan terkini terkait isu tersebut untuk dicermati pembaca."

    def _build_grounded_summary(
        self,
        query: str,
        articles: List[Dict[str, Any]],
        compared_articles: List[Dict[str, Any]]
    ) -> str:
        """
        Menyusun ringkasan komparatif yang 100% berakar pada artikel nyata yang dirujuk.
        Setiap media dan isu yang disebut dijamin konsisten dengan daftar berita asli dan tabel.
        """
        publishers = []
        for art in articles:
            pub = (art.get("publisher") or "Media Daring").strip()
            if pub not in publishers:
                publishers.append(pub)

        themes = self._extract_common_themes(query, articles)
        all_sources: List[str] = []
        all_figures: List[str] = []

        media_angles: List[str] = []
        for art in compared_articles:
            pub = (art.get("publisher") or "Media Daring").strip()
            title = self._clean_title(art.get("title", ""), pub)
            body = self._get_meaningful_body(art)
            srcs = self._extract_sources(body, title)
            figs = self._extract_figures(f"{title} {body}")
            for s in srcs:
                if s not in all_sources:
                    all_sources.append(s)
            for f in figs:
                if f not in all_figures:
                    all_figures.append(f)

            if body:
                lead = self._extract_article_focus(art).rstrip(".")
                media_angles.append(f"{pub} dalam laporannya \"{title}\" menekankan bahwa {lead[0].lower() + lead[1:] if len(lead) > 1 else lead}")
            else:
                media_angles.append(f"{pub} menyoroti isu \"{title}\"")

        # Kalimat 1: Penjelasan topik aktual berdasarkan kumpulan berita nyata
        pub_list_str = ", ".join(publishers[:4])
        if len(publishers) > 4:
            pub_list_str += f", dan {len(publishers) - 4} media lainnya"

        lead_titles = [self._clean_title(a.get("title", ""), a.get("publisher", "")) for a in compared_articles[:2] if a.get("title")]
        theme_hint = f" (antara lain terkait {', '.join(themes[:4])})" if themes else ""

        p1 = (
            f"Pencarian topik '{query}' merangkum {len(articles)} berita terkini dari {pub_list_str}{theme_hint}. "
            + (
                f"Isu utama yang mengemuka dalam liputan tersebut berpusat pada \"{lead_titles[0]}\""
                + (f" serta perkembangan mengenai \"{lead_titles[1]}\"." if len(lead_titles) > 1 else ".")
                if lead_titles else ""
            )
        ).strip()

        # Kalimat 2: Sorotan masing-masing media yang ADA di tabel perbandingan
        p2 = ""
        if media_angles:
            if len(media_angles) == 1:
                p2 = media_angles[0] + "."
            elif len(media_angles) == 2:
                p2 = f"{media_angles[0]}, sedangkan {media_angles[1]}."
            else:
                p2 = f"{media_angles[0]}; {media_angles[1]}; sementara {media_angles[2]}."

        # Kalimat 3: Aktor/narasumber & angka kunci + perbedaan penekanan
        extra_bits = []
        if all_sources:
            extra_bits.append(f"Tokoh atau lembaga yang mencuat dalam pemberitaan meliputi {', '.join(all_sources[:4])}")
        if all_figures:
            extra_bits.append(f"dengan angka/data yang dikutip berupa {', '.join(all_figures[:3])}")

        p3 = (
            (" ".join(extra_bits) + ". ") if extra_bits else ""
        ) + (
            f"Secara keseluruhan, masing-masing media di atas menampilkan sudut pandang berbeda dalam membingkai isu '{query}', "
            f"baik dari sisi dinamika aktor utama, pernyataan tokoh, maupun dampaknya bagi publik."
        )

        return f"{p1}\n\n{p2} {p3}".strip()

    def compare_cluster(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        is_absurd, _ = is_absurd_or_invalid_topic(query)
        if is_absurd:
            return {
                "query": query,
                "invalid_topic": True,
                "summary": ABSURD_TOPIC_MESSAGE,
                "matrix_columns": [],
                "matrix_rows": [],
                "consensus": [],
                "divergence": []
            }

        if not articles:
            return {
                "query": query,
                "invalid_topic": False,
                "summary": (
                    f"Topik '{query}' belum memiliki liputan yang cukup dari sumber berita aktif saat ini, "
                    "sehingga ringkasan komparatif dan matriks antarmedia belum dapat disusun. "
                    "Coba gunakan kata kunci yang lebih spesifik atau periksa topik terkait lainnya."
                ),
                "matrix_columns": ["Aspek", "Media 1", "Media 2", "Media 3"],
                "matrix_rows": [
                    {"aspek": "Data angka", "cnn": "-", "cnbc": "-", "tempo": "-"},
                    {"aspek": "Narasumber", "cnn": "-", "cnbc": "-", "tempo": "-"},
                    {"aspek": "Fokus berita", "cnn": "-", "cnbc": "-", "tempo": "-"}
                ],
                "consensus": [],
                "divergence": []
            }

        compared = self._select_comparison_articles(articles, max_slots=3)
        slot_keys = ["cnn", "cnbc", "tempo"]

        col_labels = ["Aspek"]
        for idx, key in enumerate(slot_keys):
            if idx < len(compared):
                col_labels.append((compared[idx].get("publisher") or f"Media {idx + 1}").strip())
            else:
                col_labels.append(f"Media {idx + 1}")

        row_angka = {"aspek": "Data angka"}
        row_narasumber = {"aspek": "Narasumber"}
        row_fokus = {"aspek": "Fokus berita"}

        for idx, key in enumerate(slot_keys):
            if idx < len(compared):
                art = compared[idx]
                pub = (art.get("publisher") or f"Media {idx + 1}").strip()
                title = self._clean_title(art.get("title", ""), pub)
                body = self._get_meaningful_body(art)
                full_corpus = f"{title}. {body}".strip()

                figures = self._extract_figures(full_corpus)
                sources = self._extract_sources(body, title)
                fokus = self._extract_article_focus(art)

                if figures:
                    row_angka[key] = ", ".join(figures)
                else:
                    short_title = title[:55] + ("..." if len(title) > 55 else "")
                    row_angka[key] = f"Tidak ada angka spesifik; menyoroti aspek kualitatif \"{short_title}\""

                if sources:
                    row_narasumber[key] = ", ".join(sources)
                else:
                    row_narasumber[key] = f"Subjek pemberitaan pada \"{title[:55]}{'...' if len(title) > 55 else ''}\""

                row_fokus[key] = fokus
            else:
                row_angka[key] = "-"
                row_narasumber[key] = "-"
                row_fokus[key] = "-"

        summary = self._build_grounded_summary(query, articles, compared)

        return {
            "query": query,
            "invalid_topic": False,
            "summary": summary,
            "matrix_columns": col_labels,
            "matrix_rows": [row_angka, row_narasumber, row_fokus],
            "consensus": [
                f"Seluruh laporan yang dirujuk sama-sama menyoroti perkembangan terkait '{query}'.",
                "Setiap media mengangkat konteks peristiwa berdasarkan aktor dan pernyataan yang relevan."
            ],
            "divergence": [
                "Perbedaan penekanan isu utama, narasumber yang ditonjolkan, serta sudut pandang pemberitaan antarportal."
            ]
        }


# Singleton instance
ai_engine = PrototypeAIEngine()
