"""
Prototype AI Engine (Behind The Headline)
Menyediakan simulasi NLP cerdas untuk ekstraksi aspek komparasi antarmedia:
- Ringkasan Topik Tematik (menjelaskan klasifikasi topik berita, misal: ekspor masuk ke topik Ekonomi)
- Ringkasan Artikel
- Matriks Komparasi Aspek (Data angka, Narasumber, Fokus berita)
- Executive AI Summary
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from backend.ai_engine.base import BaseAIEngine

logger = logging.getLogger("PrototypeAIEngine")

class PrototypeAIEngine(BaseAIEngine):
    """
    Mesin AI Prototype berbasis heuristik komparasi semantik.
    """

    def summarize_topic(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan topik berita secara tematik dan klasifikasinya.
        Sesuai permintaan: 'seperti berita ekspor masuk ke dalam topik ekonomi'.
        """
        title = article.get("title", "")
        publisher = article.get("publisher", "Media Daring")
        category = article.get("category", "Nasional")
        full_text = article.get("full_text", "") or article.get("snippet", "")
        combined = f"{title} {full_text} {category}".lower()

        # Pemetaan deteksi topik cerdas
        if any(k in combined for k in ["ekspor", "impor", "perdagangan", "ppn", "pajak", "rupiah", "ihsg", "inflasi", "saham", "ritel", "devisa", "komoditas", "fiskal", "apbn", "bank"]):
            subtopik = "Ekonomi & Perdagangan"
            alasan = "membahas aktivitas perdagangan komoditas, dinamika pasar, atau kebijakan fiskal yang berdampak pada stabilitas perekonomian nasional"
        elif any(k in combined for k in ["pidato", "prabowo", "gibran", "jokowi", "presiden", "wapres", "menteri", "dpr", "kpu", "pilkada", "partai", "koalisi", "oposisi", "gerindra", "kebijakan pemerintah"]):
            subtopik = "Politik & Tata Kelola Pemerintahan"
            alasan = "menyoroti dinamika kepemimpinan nasional, komunikasi pejabat publik, serta relasi kekuasaan dalam tata kelola pemerintahan"
        elif any(k in combined for k in ["hukum", "kpk", "polisi", "kejaksaan", "tersangka", "sidang", "korupsi", "hakim", "vonis", "kasus", "penyidik", "perampasan aset"]):
            subtopik = "Hukum & Penegakan Keadilan"
            alasan = "mengulas proses peradilan, perkara tindak pidana, serta komitmen penegakan aturan hukum di Indonesia"
        elif any(k in combined for k in ["ai", "teknologi", "digital", "siber", "data center", "gadget", "aplikasi", "kominfo", "komdigi", "internet"]):
            subtopik = "Teknologi & Transformasi Digital"
            alasan = "mengulas perkembangan inovasi komputasi modern, regulasi keamanan siber, dan adopsi ekosistem digital"
        elif any(k in combined for k in ["banjir", "cuaca", "iklim", "gempa", "hujan", "ciliwung", "lingkungan", "sampah", "polusi", "karhutla", "walhi"]):
            subtopik = "Lingkungan & Keberlanjutan Ekologis"
            alasan = "membahas kondisi ekologis, mitigasi krisis iklim, serta kesiapsiagaan infrastruktur terhadap tantangan lingkungan hidup"
        else:
            subtopik = f"{category} & Isu Publik"
            alasan = f"mengangkat dinamika sosial dan kebijakan strategis yang berkaitan erat dengan sektor {category}"

        return (
            f"Topik: {subtopik}. "
            f"Berita ini diklasifikasikan ke dalam ranah {subtopik} karena {alasan} berdasarkan pelaporan {publisher}."
        )

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
                p1 = paras[0]
                p2 = paras[1]
                p1_clean = re.sub(r"^[A-Z][a-zA-Z\s]+,\s*[A-Za-z0-9\.\s]+--\s*", "", p1)
                return f"{p1_clean} Laporan {publisher} lebih lanjut menyoroti bahwa {p2[:180]}..."

        if snippet:
            return f"Berdasarkan laporan {publisher}, {snippet} Topik ini menjadi sorotan penting karena berdampak langsung pada kepentingan publik dan kebijakan terkait."

        return f"Artikel {publisher} berjudul '{title}' membahas dinamika terkini dari sudut pandang kebijakan dan dampaknya terhadap masyarakat."

    def _extract_figures(self, text: str) -> List[str]:
        patterns = [
            r"Rp\s?[\d\.,]+(?:\s?(?:triliun|miliar|juta|ribu))?",
            r"[\d\.,]+\s?%",
            r"[\d\.,]+\s?(?:persen|triliun|miliar|juta|ribu|kilometer|jam|orang)"
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
        if "regulasi" in combined or "uu " in combined or "pemerintah" in combined or "kemenkeu" in combined:
            return "Kepatuhan regulasi, amanat undang-undang, dan stabilitas fiskal negara"
        elif "daya beli" in combined or "pasar" in combined or "inflasi" in combined or "ritel" in combined or "saham" in combined:
            return "Dampak ekonomi makro, inflasi, sentimen pasar, dan kelangsungan dunia usaha"
        elif "buruh" in combined or "masyarakat" in combined or "warga" in combined or "walhi" in combined or "rakyat" in combined:
            return "Beban sosial masyarakat kelas menengah, penolakan pekerja, dan kelestarian lingkungan"
        else:
            return f"Sorotan terhadap dinamika kebijakan dan kepastian tindak lanjut dari sisi {publisher}"

    def compare_cluster(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not articles:
            return {
                "query": query,
                "summary": f"Belum ditemukan cukup artikel mengenai topik '{query}' untuk dianalisis oleh AI.",
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

        row_angka = {"aspek": "Data angka"}
        row_narasumber = {"aspek": "Narasumber"}
        row_fokus = {"aspek": "Fokus berita"}

        for key in ["cnn", "cnbc", "tempo"]:
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
            summary = (
                "Pemberitaan mengenai penyesuaian tarif PPN 12% menunjukkan perbedaan sudut pandang antarmedia. "
                "CNN Indonesia menitikberatkan pada kepatuhan amanat UU HPP serta pembebasan barang kebutuhan pokok, "
                "CNBC Indonesia menyoroti kekhawatiran pengusaha ritel terhadap potensi penurunan konsumsi dan inflasi, "
                "sementara Tempo memberi porsi besar pada kritik ekonom dan penolakan serikat buruh terkait beban kelas menengah."
            )
            row_angka["cnn"] = "Tarif PPN 12%; proyeksi penerimaan negara Rp 70-80 triliun"
            row_angka["cnbc"] = "Potensi koreksi konsumsi 1,2%; tambahan inflasi 0,3-0,5%"
            row_angka["tempo"] = "Kenaikan biaya hidup urban 2,8-3,5%; 9,4 juta kelas menengah rentan"

            row_narasumber["cnn"] = "Menteri Keuangan Sri Mulyani, Ditjen Pajak"
            row_narasumber["cnbc"] = "Ketua Aprindo Roy Nicholas Mandey, Analis Pasar Modal"
            row_narasumber["tempo"] = "Direktur Celios Bhima Yudhistira, Presiden KSPI Said Iqbal"

            row_fokus["cnn"] = "Amanat regulasi UU HPP & perlindungan bansos"
            row_fokus["cnbc"] = "Sentimen ritel, inflasi, & margin emiten FMCG"
            row_fokus["tempo"] = "Daya beli kelas menengah & penolakan serikat pekerja"
        elif "banjir" in q_low or "ciliwung" in q_low:
            summary = (
                "Liputan banjir Jakarta memperlihatkan pendekatan pelaporan yang bervariasi. "
                "CNN Indonesia fokus pada percepatan normalisasi sodetan Ciliwung dan alokasi anggaran pembebasan lahan, "
                "CNBC Indonesia mengulas kerugian perputaran logistik puluhan miliar rupiah bagi dunia usaha, "
                "sedangkan Tempo menyoroti kritik Walhi terhadap solusi betonisasi dan minimnya ruang terbuka hijau."
            )
        else:
            titles = [a.get("title", "") for a in articles[:3]]
            summary = (
                f"Analisis komparatif untuk isu '{query}' mencakup berbagai perspektif media. "
                f"Pemberitaan utama membahas '{titles[0]}' dengan fokus kebijakan dan respons para pihak terkait. "
                f"Media menyajikan perbedaan penekanan pada data angka dan pemilihan narasumber kunci, "
                f"namun tetap sepakat mengenai urgensi tindak lanjut permasalahan ini bagi kepentingan masyarakat."
            )

        return {
            "query": query,
            "summary": summary,
            "matrix_columns": ["Aspek", "CNN", "CNBC", "Tempo"],
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
