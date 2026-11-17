"""
Prototype AI Engine (Behind The Headline)
Menyediakan simulasi NLP cerdas untuk ekstraksi aspek komparasi antarmedia:
- Ringkasan Topik Tematik (menjelaskan klasifikasi topik dan konteks substansinya)
- Ringkasan Artikel
- Matriks Komparasi Aspek (Data angka, Narasumber, Fokus berita)
- Executive AI Summary yang menjelaskan topik yang dicari secara mendalam
- Penolakan topik nyeleneh/tidak masuk akal
"""

import re
import logging
from typing import List, Dict, Any
from backend.ai_engine.base import BaseAIEngine
from backend.ai_engine.topic_validator import (
    ABSURD_TOPIC_MESSAGE,
    is_absurd_or_invalid_topic,
)

logger = logging.getLogger("PrototypeAIEngine")


class PrototypeAIEngine(BaseAIEngine):
    """
    Mesin AI Prototype berbasis heuristik komparasi semantik.
    """

    def _clean_lead_text(self, text: str) -> str:
        cleaned = re.sub(r"^[A-Z][a-zA-Z\s]+,\s*[A-Za-z0-9\.\s]+--\s*", "", (text or "").strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def summarize_topic(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan topik berita secara tematik, klasifikasi,
        serta penjelasan konteks substansi topik yang dibahas.
        """
        title = (article.get("title", "") or "").strip()
        publisher = (article.get("publisher", "Media Daring") or "Media Daring").strip()
        category = (article.get("category", "Nasional") or "Nasional").strip()
        full_text = article.get("full_text", "") or article.get("snippet", "")
        combined = f"{title} {full_text} {category}".lower()

        if any(k in combined for k in ["ekspor", "impor", "perdagangan", "ppn", "pajak", "rupiah", "ihsg", "inflasi", "saham", "ritel", "devisa", "komoditas", "fiskal", "apbn", "bank", "ekonomi"]):
            subtopik = "Ekonomi & Perdagangan"
            alasan = "membahas aktivitas perdagangan komoditas, kebijakan fiskal/perpajakan, atau dinamika pasar yang berdampak langsung pada daya beli dan stabilitas perekonomian nasional"
            dampak = "Pemahaman atas topik ini membantu pembaca melihat keterkaitan antara kebijakan pemerintah, sentimen pelaku usaha, dan beban biaya hidup masyarakat."
        elif any(k in combined for k in ["pidato", "prabowo", "gibran", "jokowi", "presiden", "wapres", "menteri", "dpr", "kpu", "pilkada", "pemilu", "partai", "koalisi", "oposisi", "gerindra", "politik", "kebijakan pemerintah"]):
            subtopik = "Politik & Tata Kelola Pemerintahan"
            alasan = "menyoroti dinamika kepemimpinan nasional, proses elektoral, serta pengambilan keputusan strategis di ranah pemerintahan dan parlemen"
            dampak = "Isu ini penting dicermati untuk menilai akuntabilitas pejabat publik, arah kebijakan negara, serta dampaknya terhadap stabilitas demokrasi."
        elif any(k in combined for k in ["hukum", "kpk", "polisi", "kejaksaan", "tersangka", "sidang", "korupsi", "hakim", "vonis", "kasus", "penyidik", "perampasan aset", "uu "]):
            subtopik = "Hukum & Penegakan Keadilan"
            alasan = "mengulas proses penyidikan, peradilan perkara tindak pidana, serta upaya penguatan regulasi dan pemberantasan korupsi di Indonesia"
            dampak = "Perkembangan isu ini berpengaruh langsung pada tingkat kepercayaan publik, kepastian hukum bagi dunia usaha, serta integritas lembaga penegak hukum."
        elif any(k in combined for k in ["ai", "kecerdasan buatan", "teknologi", "digital", "siber", "data center", "gadget", "aplikasi", "kominfo", "komdigi", "internet"]):
            subtopik = "Teknologi & Transformasi Digital"
            alasan = "mengulas perkembangan inovasi komputasi modern, infrastruktur pusat data, tata kelola etika digital, serta keamanan siber"
            dampak = "Topik ini krusial karena menyangkut kesiapan tenaga kerja, perlindungan data pribadi, dan daya saing ekonomi digital nasional."
        elif any(k in combined for k in ["banjir", "cuaca", "iklim", "gempa", "hujan", "ciliwung", "lingkungan", "sampah", "polusi", "karhutla", "walhi", "resapan"]):
            subtopik = "Lingkungan & Keberlanjutan Ekologis"
            alasan = "membahas kondisi ekologis, mitigasi risiko bencana hidrometeorologi, serta tata ruang dan kesiapsiagaan infrastruktur perkotaan"
            dampak = "Pembahasan topik ini menyoroti keseimbangan antara pembangunan fisik, pelestarian ekosistem, dan keselamatan warga terdampak."
        else:
            subtopik = f"{category} & Isu Publik"
            alasan = f"mengangkat dinamika sosial dan kebijakan strategis yang berkaitan erat dengan sektor {category}"
            dampak = "Topik ini memberi gambaran kontekstual bagi pembaca untuk membandingkan fokus pemberitaan lintas media."

        figures = self._extract_figures(f"{title} {full_text}")
        sources = self._extract_sources(f"{title} {full_text}")
        detail_parts = []
        if title:
            detail_parts.append(f"Secara khusus, laporan {publisher} berjudul \"{title}\" menyoroti inti persoalan ini")
        if sources:
            detail_parts.append(f"dengan merujuk keterangan dari {', '.join(sources[:2])}")
        if figures:
            detail_parts.append(f"serta mencantumkan indikator angka penting ({', '.join(figures[:2])})")

        detail_sentence = (" ".join(detail_parts) + ".") if detail_parts else ""

        return (
            f"Topik: {subtopik}. "
            f"Berita ini diklasifikasikan ke dalam ranah {subtopik} karena {alasan} berdasarkan pelaporan {publisher}. "
            f"{detail_sentence} {dampak}"
        ).strip()

    def summarize_article(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan intisari artikel berita.
        """
        title = article.get("title", "")
        publisher = article.get("publisher", "Media")
        full_text = article.get("full_text", "")
        snippet = article.get("snippet", "")

        if full_text:
            paras = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 30]
            if len(paras) >= 2:
                p1_clean = self._clean_lead_text(paras[0])
                p2_clean = self._clean_lead_text(paras[1])
                return f"{p1_clean} Laporan {publisher} lebih lanjut menyoroti bahwa {p2_clean[:220]}"

        if snippet:
            return f"Berdasarkan laporan {publisher}, {self._clean_lead_text(snippet)} Topik ini menjadi sorotan penting karena berdampak langsung pada kepentingan publik dan kebijakan terkait."

        return f"Artikel {publisher} berjudul '{title}' membahas dinamika terkini dari sudut pandang kebijakan dan dampaknya terhadap masyarakat."

    def _extract_figures(self, text: str) -> List[str]:
        patterns = [
            r"Rp\s?[\d\.,]+(?:\s?(?:triliun|miliar|juta|ribu))?",
            r"[\d\.,]+\s?%",
            r"[\d\.,]+\s?(?:persen|triliun|miliar|juta|ribu|kilometer|jam|orang|daerah)"
        ]
        found = []
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip()
                if clean_m not in found and len(clean_m) > 1:
                    found.append(clean_m)
        return found[:4]

    def _extract_sources(self, text: str) -> List[str]:
        sources = []
        keywords = [
            r"(?:Menteri|Menkeu|Ketua|Direktur|Kepala|Presiden|Pakar|Pengamat|Juru Bicara)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*",
            r"(?:ujar|kata|tegas|menurut|tutur)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        for kw in keywords:
            matches = re.findall(kw, text)
            for m in matches:
                name = m.strip() if isinstance(m, str) else m[0].strip()
                if name and name not in sources and len(name) > 4:
                    sources.append(name)
        return sources[:3]

    def _detect_framing(self, publisher: str, text: str, title: str) -> str:
        combined = f"{title} {text}".lower()
        if "regulasi" in combined or "uu " in combined or "pemerintah" in combined or "kemenkeu" in combined or "kpu" in combined:
            return "Kepatuhan regulasi, kebijakan pemerintah, dan kesiapan tata kelola institusi"
        elif "daya beli" in combined or "pasar" in combined or "inflasi" in combined or "ritel" in combined or "saham" in combined or "investasi" in combined:
            return "Dampak ekonomi makro, inflasi, sentimen pelaku usaha/pasar, dan iklim investasi"
        elif "buruh" in combined or "masyarakat" in combined or "warga" in combined or "walhi" in combined or "rakyat" in combined or "korupsi" in combined:
            return "Dampak sosial langsung pada masyarakat, kritik pengamat, dan akuntabilitas publik"
        else:
            return f"Sorotan terhadap perkembangan fakta lapangan dan tindak lanjut isu oleh {publisher}"

    def _build_dynamic_summary(self, query: str, articles: List[Dict[str, Any]]) -> str:
        """Menyusun ringkasan penjelasan topik yang kaya berdasarkan artikel yang ditemukan."""
        q_low = query.lower().strip()

        if "ppn" in q_low or "pajak" in q_low:
            return (
                "Topik ini membahas rencana penyesuaian tarif Pajak Pertambahan Nilai (PPN) dari 11% menjadi 12% sesuai amanat UU Harmonisasi Peraturan Perpajakan (UU HPP) yang berlaku mulai 2025. "
                "Secara substansi, kebijakan ini bertujuan menambah penerimaan fiskal negara sekitar Rp 70–80 triliun untuk membiayai perlindungan sosial dan infrastruktur, dengan pengecualian bagi kebutuhan pokok, kesehatan, serta pendidikan. "
                "Dalam liputannya, media memiliki penekanan berbeda: CNN Indonesia menitikberatkan pada landasan regulasi pemerintah dan jaring pengaman sosial, CNBC Indonesia menyoroti kekhawatiran pelaku ritel atas potensi koreksi konsumsi 1,2% dan tekanan inflasi, "
                "sementara Tempo menggarisbawahi kritik ekonom serta serikat buruh mengenai meningkatnya beban biaya hidup kelas menengah."
            )
        if "banjir" in q_low or "ciliwung" in q_low:
            return (
                "Topik ini mengulas penanganan banjir Jakarta, khususnya percepatan proyek normalisasi Sungai Ciliwung serta perdebatan efektivitas solusi infrastruktur menghadapi curah hujan ekstrem. "
                "Permasalahan utama meliputi pembebasan lahan bantaran sungai senilai Rp 850 miliar, gangguan rantai pasok logistik yang memicu kerugian puluhan miliar rupiah per hari, dan minimnya luas Ruang Terbuka Hijau (RTH) di bawah 10%. "
                "CNN Indonesia memfokuskan pemberitaan pada progres pengerjaan polder serta anggaran pemerintah daerah, CNBC Indonesia menekankan dampak ekonomi bagi dunia usaha dan distribusi barang, "
                "sedangkan Tempo mengangkat kritik pegiat lingkungan (Walhi) terhadap pendekatan betonisasi sungai yang dinilai belum menyentuh krisis resapan air dari hulu ke hilir."
            )
        if q_low in {"politik", "pilkada", "pemilu"}:
            return (
                "Topik Politik yang dicari menyoroti dinamika penyelenggaraan Pilkada Serentak di ratusan daerah Indonesia, mulai dari kesiapan logistik pemungutan suara, dampak ekonomi lokal, hingga pengawasan integritas pemilu. "
                "Isu sentralnya mencakup distribusi surat suara ke wilayah 3T oleh KPU, aliran likuiditas belanja kampanye ke sektor percetakan dan perhotelan daerah, serta pemetaan ratusan kabupaten/kota rawan politik uang dan pelanggaran netralitas ASN. "
                "CNN Indonesia menyoroti aspek teknis kesiapan logistik dan pengawalan aparat, CNBC Indonesia menelaah kontribusi stimulus belanja kampanye terhadap PDB daerah, "
                "sementara Tempo menyoroti temuan Bawaslu terkait potensi penyalahgunaan wewenang petahana."
            )
        if q_low in {"ekonomi", "ekspor", "inflasi"}:
            return (
                "Topik Ekonomi yang dicari menjelaskan kebijakan fiskal, pergerakan konsumsi domestik, dan sentimen pelaku pasar terhadap daya beli masyarakat Indonesia. "
                "Pembahasan utamanya berkisar pada penyesuaian instrumen perpajakan negara, proyeksi target penerimaan APBN, serta risiko kenaikan biaya operasional bagi industri ritel dan sektor barang konsumsi. "
                "Dari sudut pandang media, CNN Indonesia lebih banyak mengutip penjelasan resmi Kementerian Keuangan terkait perlindungan masyarakat rentan, CNBC Indonesia menganalisis proyeksi margin emiten dan risiko inflasi, "
                "sedangkan Tempo menyoroti kerentanan ekonomi kelompok kelas menengah dan tuntutan serikat pekerja."
            )
        if q_low in {"hukum", "korupsi", "kpk"}:
            return (
                "Topik Hukum yang dicari membahas agenda penegakan hukum dan pemberantasan tindak pidana korupsi, termasuk upaya pemulihan aset negara (asset recovery) serta desakan pengesahan RUU Perampasan Aset. "
                "Persoalan ini menjadi perhatian luas karena menyangkut efektivitas penyitaan aset bernilai ratusan miliar rupiah, perbaikan skor Indeks Persepsi Korupsi, serta kepastian hukum bagi iklim investasi nasional. "
                "CNN Indonesia menyoroti langkah teknis penyidikan dan penyitaan aset oleh KPK, CNBC Indonesia menekankan keterkaitan kepastian hukum dengan kepercayaan investor asing, "
                "dan Tempo mengkritisi stagnasi reformasi kelembagaan serta potensi konflik kepentingan di legislatif."
            )
        if q_low in {"teknologi", "ai", "digital"}:
            return (
                "Topik Teknologi yang dicari membahas percepatan adopsi kecerdasan buatan (AI) di Indonesia beserta tata kelola etika, gelombang investasi pusat data (data center), dan dampaknya terhadap pasar tenaga kerja. "
                "Fokus utamanya mencakup penyusunan peta jalan etika Generative AI oleh pemerintah guna melindungi privasi serta hak cipta, masuknya investasi hyperscale data center senilai puluhan triliun rupiah, dan risiko otomasi pekerjaan administratif. "
                "CNN Indonesia mengulas kerangka regulasi dan mitigasi deepfake, CNBC Indonesia menyoroti nilai investasi infrastruktur digital di Cikarang dan Batam, "
                "sedangkan Tempo mengangkat urgensi kedaulatan data serta program reskilling pekerja muda."
            )
        if q_low in {"lingkungan", "iklim", "sampah"}:
            return (
                "Topik Lingkungan yang dicari mengulas tantangan tata kelola ekologis dan mitigasi bencana hidrometeorologi di kawasan perkotaan, terutama banjir, tata ruang, dan ketersediaan daerah resapan air. "
                "Pembahasan menyoroti kontras antara proyek rekayasa fisik seperti normalisasi tanggul sungai, dampak kerugian ekonomi akibat gangguan logistik, dan krisis ruang terbuka hijau yang baru mencapai 9,8% di ibu kota. "
                "CNN Indonesia berfokus pada upaya teknis pemerintah daerah mempercepat pengendalian genangan, CNBC Indonesia menghitung kerugian ekonomi dunia usaha, "
                "sementara Tempo menekankan perlunya restorasi ekosistem hulu ke hilir."
            )

        # Sintesis dinamis berbasis konten artikel aktual untuk topik umum apa pun
        publishers = []
        highlights = []
        all_figures = []
        all_sources = []

        for art in articles[:4]:
            pub = art.get("publisher", "Media")
            title = (art.get("title", "") or "").strip()
            snippet = self._clean_lead_text(art.get("snippet", "") or art.get("full_text", ""))
            if pub and pub not in publishers:
                publishers.append(pub)
            if title:
                if snippet and len(snippet) > 40 and snippet.lower() not in title.lower():
                    highlights.append(f"{pub} mengangkat \"{title}\" dengan sorotan pada {snippet[:140].rstrip('.')}...")
                else:
                    highlights.append(f"{pub} menyoroti perkembangan \"{title}\"")
            corpus = f"{title} {snippet}"
            for f in self._extract_figures(corpus):
                if f not in all_figures:
                    all_figures.append(f)
            for s in self._extract_sources(corpus):
                if s not in all_sources:
                    all_sources.append(s)

        intro = (
            f"Topik '{query}' mengulas perkembangan isu terkini yang sedang menjadi sorotan di {len(articles)} laporan media nasional"
            + (f" ({', '.join(publishers[:3])}). " if publishers else ". ")
        )
        substance = " ".join(highlights[:2]) + (" " if highlights else "")
        context_bits = []
        if all_sources:
            context_bits.append(f"Pihak atau narasumber yang mencuat dalam pemberitaan antara lain {', '.join(all_sources[:3])}")
        if all_figures:
            context_bits.append(f"dengan data penting berupa {', '.join(all_figures[:3])}")
        context_sentence = (". ".join(context_bits) + ". ") if context_bits else ""
        closing = (
            "Secara keseluruhan, masing-masing portal menempatkan penekanan berbeda—mulai dari aspek regulasi dan kronologi peristiwa hingga dampak sosial-ekonominya bagi masyarakat."
        )
        return (intro + substance + context_sentence + closing).strip()

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
                "matrix_columns": ["Aspek", "CNN", "CNBC", "Tempo"],
                "matrix_rows": [
                    {"aspek": "Data angka", "cnn": "-", "cnbc": "-", "tempo": "-"},
                    {"aspek": "Narasumber", "cnn": "-", "cnbc": "-", "tempo": "-"},
                    {"aspek": "Fokus berita", "cnn": "-", "cnbc": "-", "tempo": "-"}
                ],
                "consensus": [],
                "divergence": []
            }

        media_data: Dict[str, Dict[str, Any]] = {
            "cnn": None,
            "cnbc": None,
            "tempo": None
        }
        other_media: List[Dict[str, Any]] = []

        for art in articles:
            pub_lower = art.get("publisher", "").lower()
            if "cnn" in pub_lower and not media_data["cnn"]:
                media_data["cnn"] = art
            elif "cnbc" in pub_lower and not media_data["cnbc"]:
                media_data["cnbc"] = art
            elif "tempo" in pub_lower and not media_data["tempo"]:
                media_data["tempo"] = art
            else:
                other_media.append(art)

        slot_keys = ["cnn", "cnbc", "tempo"]
        for key in slot_keys:
            if not media_data[key] and other_media:
                media_data[key] = other_media.pop(0)

        col_labels = ["Aspek"]
        default_labels = {"cnn": "CNN", "cnbc": "CNBC", "tempo": "Tempo"}
        for key in slot_keys:
            art = media_data[key]
            if art and art.get("publisher"):
                col_labels.append(art["publisher"])
            else:
                col_labels.append(default_labels[key])

        row_angka = {"aspek": "Data angka"}
        row_narasumber = {"aspek": "Narasumber"}
        row_fokus = {"aspek": "Fokus berita"}

        for key in slot_keys:
            art = media_data[key]
            if art:
                text = f"{art.get('title', '')} {art.get('snippet', '')} {art.get('full_text', '')}"
                figures = self._extract_figures(text)
                sources = self._extract_sources(text)
                fokus = self._detect_framing(art.get("publisher", key.upper()), text, art.get("title", ""))

                row_angka[key] = ", ".join(figures) if figures else "Statistik kualitatif / regulasi"
                row_narasumber[key] = ", ".join(sources) if sources else f"Koresponden {art.get('publisher', key.upper())}"
                row_fokus[key] = fokus
            else:
                row_angka[key] = "Data angka tidak disorot"
                row_narasumber[key] = "Pernyataan redaksi"
                row_fokus[key] = "Belum memuat liputan mendalam"

        q_low = query.lower()
        if "ppn" in q_low or "pajak" in q_low:
            row_angka["cnn"] = "Tarif PPN 12%; proyeksi penerimaan negara Rp 70-80 triliun"
            row_angka["cnbc"] = "Potensi koreksi konsumsi 1,2%; tambahan inflasi 0,3-0,5%"
            row_angka["tempo"] = "Kenaikan biaya hidup urban 2,8-3,5%; 9,4 juta kelas menengah rentan"

            row_narasumber["cnn"] = "Menteri Keuangan Sri Mulyani, Ditjen Pajak"
            row_narasumber["cnbc"] = "Ketua Aprindo Roy Nicholas Mandey, Analis Pasar Modal"
            row_narasumber["tempo"] = "Direktur Celios Bhima Yudhistira, Presiden KSPI Said Iqbal"

            row_fokus["cnn"] = "Amanat regulasi UU HPP & perlindungan bansos"
            row_fokus["cnbc"] = "Sentimen ritel, inflasi, & margin emiten FMCG"
            row_fokus["tempo"] = "Daya beli kelas menengah & penolakan serikat pekerja"

        summary = self._build_dynamic_summary(query, articles)

        return {
            "query": query,
            "invalid_topic": False,
            "summary": summary,
            "matrix_columns": col_labels,
            "matrix_rows": [row_angka, row_narasumber, row_fokus],
            "consensus": [
                f"Semua media sepakat bahwa isu '{query}' memiliki dampak signifikan dan menjadi perhatian publik.",
                "Terdapat pengakuan bersama mengenai perlunya koordinasi lintas sektor dalam implementasi kebijakan."
            ],
            "divergence": [
                "Perbedaan sudut pandang antara kepatuhan regulasi pemerintah vs dampak daya beli riil masyarakat.",
                "Variasi data statistik yang dikutip: laporan resmi kementerian berbanding kajian asosiasi independen."
            ]
        }


# Singleton instance
ai_engine = PrototypeAIEngine()
