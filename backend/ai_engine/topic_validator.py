"""
Validator Topik Berita (Behind The Headline)
Mendeteksi query/topik yang nyeleneh, tidak masuk akal, acak (gibberish),
atau di luar ranah pemberitaan agar sistem tidak memaksakan hasil berita.
"""

import re
from typing import Tuple

ABSURD_TOPIC_MESSAGE = "Maaf, saya tidak dapat menyajikan berita tersebut."

# Kata kunci karakter fiksi, makhluk mitologi/mistis, dan meme/brainrot
FICTIONAL_OR_ABSURD_TERMS = {
    "alien", "ufo", "unicorn", "naga", "zombie", "vampir", "drakula",
    "pocong", "kuntilanak", "genderuwo", "tuyul", "spongebob", "patrick",
    "doraemon", "nobita", "naruto", "sasuke", "goku", "ultraman", "pikachu",
    "godzilla", "voldemort", "thanos", "skibidi", "brainrot", "santet",
    "pelet", "dukun", "jin", "iblis", "setan", "hantu", "mermaid", "duyung",
    "peri", "kurcaci", "werewolf", "frankenstein", "slenderman", "herobrine",
    "creeper", "kamen rider", "power rangers"
}

# Konteks hiburan/karya nyata yang boleh tetap dicari bila digabung kata kunci hiburan
ENTERTAINMENT_CONTEXT_TERMS = {
    "film", "movie", "anime", "manga", "komik", "serial", "game", "bioskop",
    "sutradara", "aktor", "aktris", "trailer", "box office", "rilis", "netflix"
}

# Pola aksi mustahil / nyeleneh yang melibatkan hewan atau benda mati
IMPOSSIBLE_ANIMAL_OR_OBJECT_PATTERN = re.compile(
    r"\b(kucing|anjing|sapi|kambing|ayam|bebek|ikan|semut|nyamuk|kecoa|tikus|"
    r"kodok|katak|monyet|gajah|jerapah|buaya|cicak|tokek|ular|cacing|burung|"
    r"batu|kursi|meja|sendok|galon|ember|sandal|sepatu|kulkas|kipas|sapu|"
    r"tembok|pohon|awan|bulan|matahari|planet)\b.*\b("
    r"terbang|naik motor|naik mobil|nyetir|jualan|nikah|menikah|kawin|pacaran|"
    r"korupsi|nyapres|jadi presiden|main bola|main futsal|ngopi|merokok|"
    r"berbicara|pidato|kuliah|sekolah|demo|balapan|bertelur|makan batu|"
    r"makan paku|minum bensin|main game|nonton tv|jadi menteri|jadi dpr)\b",
    re.IGNORECASE
)

# Pola frasa nyeleneh / mustahil lainnya
ABSURD_PHRASE_PATTERN = re.compile(
    r"\b(makan paku|makan batu|makan beling|goreng es|rebus es batu|"
    r"air kering|ikan tenggelam|kucing bertelur|sapi bertelur|manusia bersayap|"
    r"babi ngepet|wewe gombel|kiamat besok|matahari padam|presiden mars|"
    r"jualan di mars|nikah sama hantu|pacaran sama jin|terbang ke matahari)\b",
    re.IGNORECASE
)

# Pola obrolan/permintaan non-berita
NON_NEWS_CHAT_PATTERN = re.compile(
    r"^(\s)*(halo|hai|hi|hello|apa kabar|siapa kamu|siapa nama kamu|siapa pacar|"
    r"tolong buatkan|buatkan (puisi|cerpen|pantun|lirik|kode|program)|"
    r"resep\s+\w+|cara memasak|arti mimpi|ramalan zodiak|tebak.?tebakan)\b",
    re.IGNORECASE
)

# Keyboard mash yang umum
KEYBOARD_MASH_SUBSTRINGS = (
    "asdf", "qwer", "zxcv", "hjkl", "yuio", "uiop", "jkl", "bnm", "fghj", "dfgh"
)

# Akronim valid yang mengandung deretan konsonan
VALID_CONSONANT_WORDS = {
    "kpk", "dpr", "mpr", "dpd", "ppn", "bbm", "pssi", "bmkg", "ihsg", "umkm",
    "tni", "polri", "asn", "bumn", "bumd", "kpu", "kbri", "lpsk", "bpk", "bpkp",
    "bnpb", "brin", "pdip", "pkb", "pks", "ppp", "pan", "psi", "btn", "bri",
    "bni", "bca", "bsi", "pln", "krl", "mrt", "lrt", "ikn", "stnk", "skck",
    "npwp", "ppatk", "kuhp", "hpp", "fmcg", "kspi", "apbn", "apbd", "ojk",
    "lps", "bpjs", "bappenas", "kemenkeu", "kemendikbud", "kemenkes", "komdigi",
    "kominfo", "bawaslu", "mk", "ma", "ky", "pt", "cv", "sd", "smp", "sma",
    "smk", "sbmptn", "snbt", "utbk", "cpns", "pppk", "thr", "umr", "ump", "umk",
    "pdb", "pnbp", "rth", "tki", "pmi", "nkk", "kkn", "pkk", "rri", "tvri"
}


def is_absurd_or_invalid_topic(query: str) -> Tuple[bool, str]:
    """
    Memeriksa apakah query adalah topik berita yang valid atau topik nyeleneh/acak.
    Mengembalikan (True, alasan) jika query harus ditolak sebagai topik nyeleneh/tidak valid,
    atau (False, "") jika layak dicari sebagai topik berita.
    """
    if not query or not isinstance(query, str):
        return True, "empty_query"

    q = query.strip()
    if len(q) < 2:
        return True, "too_short"

    # Hanya angka atau tanda baca
    if re.fullmatch(r"[\d\W_]+", q):
        return True, "non_alphabetic"

    q_lower = q.lower()
    words = re.findall(r"[a-zA-Z]+", q_lower)
    if not words:
        return True, "no_words"

    # Karakter berulang terus-menerus (mis. aaaaa, wkwkwkwk, hahaha)
    if re.search(r"(.)\1{3,}", q_lower) or re.search(r"\b(wk){2,}|(ha){3,}|(he){3,}|(hi){3,}\b", q_lower):
        return True, "gibberish_repeat"

    # Deteksi keyboard mash
    for mash in KEYBOARD_MASH_SUBSTRINGS:
        if mash in q_lower and not any(w in VALID_CONSONANT_WORDS for w in words):
            return True, "keyboard_mash"

    # Deteksi kata acak tanpa vokal atau konsonan bertumpuk ekstrem
    for w in words:
        if w in VALID_CONSONANT_WORDS:
            continue
        if len(w) >= 5 and not re.search(r"[aeiou]", w):
            return True, "no_vowels_gibberish"
        if re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", w):
            return True, "consonant_cluster_gibberish"

    # Deteksi pola non-berita / obrolan santai
    if NON_NEWS_CHAT_PATTERN.search(q_lower):
        return True, "non_news_chat"

    # Deteksi frasa mustahil / hewan/benda melakukan aksi manusia/mustahil
    if IMPOSSIBLE_ANIMAL_OR_OBJECT_PATTERN.search(q_lower) or ABSURD_PHRASE_PATTERN.search(q_lower):
        return True, "absurd_scenario"

    # Deteksi entitas fiksi/mistis/meme tanpa konteks hiburan nyata
    has_entertainment_ctx = any(ctx in q_lower for ctx in ENTERTAINMENT_CONTEXT_TERMS)
    if not has_entertainment_ctx:
        for term in FICTIONAL_OR_ABSURD_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", q_lower):
                return True, f"absurd_term:{term}"

    return False, ""

