import json
import re

from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==================================================
# DOSYA YOLLARI
# ==================================================

PROJECT_FOLDER = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_FOLDER
    / "data"
    / "questions.json"
)


# ==================================================
# EŞLEŞME AYARLARI
# ==================================================

# Bu değerin altındaki eşleşmeler cevap olarak kabul edilmez.
MINIMUM_SIMILARITY_SCORE = 0.20

# Bu değerin altında kalan fakat tamamen başarısız olmayan
# eşleşmeler öneri olarak kullanıcıya gösterilebilir.
SUGGESTION_SIMILARITY_SCORE = 0.10

# Tam eşleşme için kullanılacak güven oranı.
EXACT_MATCH_CONFIDENCE = 1.0


# ==================================================
# METİN NORMALLEŞTİRME
# ==================================================

def normalize_text(text: str) -> str:
    """
    Metni karşılaştırmaya uygun hâle getirir.

    Örnek:
    'Wi-Fi Çalışmıyor!' -> 'wi fi calismiyor'
    """

    normalized_text = str(text).lower().strip()

    replacements = {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c"
    }

    for old_character, new_character in replacements.items():

        normalized_text = normalized_text.replace(
            old_character,
            new_character
        )

    normalized_text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        normalized_text
    )

    normalized_text = re.sub(
        r"\s+",
        " ",
        normalized_text
    )

    return normalized_text.strip()


def split_words(text: str) -> list[str]:
    """
    Metni normalleştirip kelimelere ayırır.
    """

    normalized_text = normalize_text(
        text
    )

    if not normalized_text:
        return []

    return normalized_text.split()


# ==================================================
# BİLGİ TABANINI OKUMA
# ==================================================

def load_questions() -> list[dict[str, Any]]:
    """
    questions.json dosyasındaki geçerli
    teknik destek kayıtlarını yükler.
    """

    try:

        with DATA_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            list
        ):

            print(
                "questions.json içeriği liste biçiminde değil."
            )

            return []

        valid_items = []

        for item in data:

            if not isinstance(
                item,
                dict
            ):
                continue

            category = str(
                item.get(
                    "category",
                    ""
                )
            ).strip()

            question = str(
                item.get(
                    "question",
                    ""
                )
            ).strip()

            answer = str(
                item.get(
                    "answer",
                    ""
                )
            ).strip()

            keywords = item.get(
                "keywords",
                []
            )

            if isinstance(
                keywords,
                str
            ):

                keywords = [
                    keyword.strip()
                    for keyword in keywords.split(",")
                    if keyword.strip()
                ]

            if not isinstance(
                keywords,
                list
            ):

                keywords = []

            cleaned_keywords = [
                str(keyword).strip()
                for keyword in keywords
                if str(keyword).strip()
            ]

            if not cleaned_keywords:

                cleaned_keywords = [
                    question
                ]

            if (
                not category
                or not question
                or not answer
            ):
                continue

            valid_items.append(
                {
                    "category": category,
                    "question": question,
                    "keywords": cleaned_keywords,
                    "answer": answer
                }
            )

        return valid_items

    except FileNotFoundError:

        print(
            "Veri dosyası bulunamadı: {}".format(
                DATA_FILE
            )
        )

        return []

    except json.JSONDecodeError as error:

        print(
            "questions.json dosyasında JSON hatası var: {}".format(
                error
            )
        )

        return []

    except OSError as error:

        print(
            "questions.json okunurken hata oluştu: {}".format(
                error
            )
        )

        return []


# ==================================================
# ARAMA METNİ HAZIRLAMA
# ==================================================

def create_search_text(
    support_item: dict[str, Any]
) -> str:
    """
    Bir destek kaydındaki soru ve anahtar
    kelimeleri tek arama metnine dönüştürür.
    """

    question = str(
        support_item.get(
            "question",
            ""
        )
    )

    keywords = support_item.get(
        "keywords",
        []
    )

    if not isinstance(
        keywords,
        list
    ):

        keywords = []

    keyword_text = " ".join(
        str(keyword)
        for keyword in keywords
    )

    # Anahtar kelimeler iki kez eklenerek
    # eşleşmedeki etkileri biraz artırılır.
    combined_text = (
        "{} {} {}".format(
            question,
            keyword_text,
            keyword_text
        )
    )

    return normalize_text(
        combined_text
    )


# ==================================================
# DOĞRUDAN EŞLEŞME
# ==================================================

def find_exact_match(
    question: str,
    category_items: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """
    Kullanıcının yazdığı metin kayıtlı soruyla
    tamamen aynıysa ilgili kaydı döndürür.
    """

    normalized_question = normalize_text(
        question
    )

    for item in category_items:

        item_question = normalize_text(
            str(
                item.get(
                    "question",
                    ""
                )
            )
        )

        if (
            normalized_question
            and normalized_question == item_question
        ):

            return item

    return None


def find_keyword_match(
    question: str,
    category_items: list[dict[str, Any]]
) -> Tuple[Optional[dict[str, Any]], float]:
    """
    Kullanıcı sorusuyla anahtar kelimeler arasındaki
    güçlü doğrudan eşleşmeyi bulur.
    """

    normalized_question = normalize_text(
        question
    )

    question_words = set(
        split_words(
            question
        )
    )

    best_item = None
    best_score = 0.0

    for item in category_items:

        keywords = item.get(
            "keywords",
            []
        )

        if not isinstance(
            keywords,
            list
        ):
            continue

        matched_keyword_count = 0
        total_keyword_count = 0

        for keyword in keywords:

            normalized_keyword = normalize_text(
                str(keyword)
            )

            if not normalized_keyword:
                continue

            total_keyword_count += 1

            keyword_words = set(
                split_words(
                    normalized_keyword
                )
            )

            phrase_match = (
                normalized_keyword
                in normalized_question
            )

            word_match = (
                bool(keyword_words)
                and keyword_words.issubset(
                    question_words
                )
            )

            if phrase_match or word_match:

                matched_keyword_count += 1

        if total_keyword_count == 0:
            continue

        keyword_score = (
            matched_keyword_count
            / total_keyword_count
        )

        if keyword_score > best_score:

            best_score = keyword_score
            best_item = item

    return (
        best_item,
        best_score
    )


# ==================================================
# TF-IDF BENZERLİĞİ
# ==================================================

def calculate_tfidf_scores(
    question: str,
    category_items: list[dict[str, Any]],
    analyzer: str,
    ngram_range: Tuple[int, int]
) -> list[float]:
    """
    Belirtilen TF-IDF ayarlarıyla bütün
    kayıtların benzerlik skorlarını hesaplar.
    """

    if not category_items:
        return []

    normalized_question = normalize_text(
        question
    )

    support_texts = [
        create_search_text(item)
        for item in category_items
    ]

    all_texts = (
        support_texts
        + [normalized_question]
    )

    try:

        vectorizer = TfidfVectorizer(
            analyzer=analyzer,
            ngram_range=ngram_range,
            lowercase=False,
            sublinear_tf=True
        )

        tfidf_matrix = vectorizer.fit_transform(
            all_texts
        )

    except ValueError:

        return [
            0.0
            for _ in category_items
        ]

    question_vector = tfidf_matrix[-1]

    support_vectors = tfidf_matrix[:-1]

    similarity_scores = cosine_similarity(
        question_vector,
        support_vectors
    ).flatten()

    return [
        float(score)
        for score in similarity_scores
    ]


def calculate_sequence_score(
    question: str,
    support_item: dict[str, Any]
) -> float:
    """
    Yazım hatalarına karşı karakter dizisi
    benzerliğini hesaplar.
    """

    normalized_question = normalize_text(
        question
    )

    item_question = normalize_text(
        str(
            support_item.get(
                "question",
                ""
            )
        )
    )

    if (
        not normalized_question
        or not item_question
    ):

        return 0.0

    return SequenceMatcher(
        None,
        normalized_question,
        item_question
    ).ratio()


def calculate_word_overlap_score(
    question: str,
    support_item: dict[str, Any]
) -> float:
    """
    Kullanıcı sorusu ile kayıt metni arasındaki
    ortak kelime oranını hesaplar.
    """

    question_words = set(
        split_words(
            question
        )
    )

    support_words = set(
        split_words(
            create_search_text(
                support_item
            )
        )
    )

    if (
        not question_words
        or not support_words
    ):

        return 0.0

    common_words = (
        question_words
        & support_words
    )

    return (
        len(common_words)
        / len(question_words)
    )


def find_best_hybrid_match(
    question: str,
    category_items: list[dict[str, Any]]
) -> Tuple[Optional[dict[str, Any]], float]:
    """
    Karakter TF-IDF, kelime TF-IDF, yazım
    benzerliği ve ortak kelime skorlarını
    birleştirerek en iyi kaydı bulur.
    """

    if not category_items:

        return (
            None,
            0.0
        )

    character_scores = calculate_tfidf_scores(
        question=question,
        category_items=category_items,
        analyzer="char_wb",
        ngram_range=(3, 5)
    )

    word_scores = calculate_tfidf_scores(
        question=question,
        category_items=category_items,
        analyzer="word",
        ngram_range=(1, 2)
    )

    final_scores = []

    for item_index, item in enumerate(
        category_items
    ):

        character_score = (
            character_scores[item_index]
            if item_index < len(character_scores)
            else 0.0
        )

        word_score = (
            word_scores[item_index]
            if item_index < len(word_scores)
            else 0.0
        )

        sequence_score = calculate_sequence_score(
            question,
            item
        )

        overlap_score = calculate_word_overlap_score(
            question,
            item
        )

        # Ağırlıkların toplamı 1'dir.
        final_score = (
            character_score * 0.40
            + word_score * 0.30
            + sequence_score * 0.15
            + overlap_score * 0.15
        )

        final_scores.append(
            final_score
        )

    if not final_scores:

        return (
            None,
            0.0
        )

    best_match_index = max(
        range(
            len(final_scores)
        ),
        key=lambda index: final_scores[index]
    )

    return (
        category_items[best_match_index],
        float(
            final_scores[best_match_index]
        )
    )


# ==================================================
# GÜVEN SKORU
# ==================================================

def convert_score_to_percentage(
    similarity_score: float
) -> int:
    """
    0 ile 1 arasındaki benzerlik skorunu
    yüzde değerine dönüştürür.
    """

    limited_score = max(
        0.0,
        min(
            similarity_score,
            1.0
        )
    )

    return int(
        round(
            limited_score * 100
        )
    )


def get_confidence_level(
    similarity_score: float
) -> str:
    """
    Benzerlik skoruna göre güven seviyesini
    metin olarak döndürür.
    """

    if similarity_score >= 0.70:
        return "Yüksek"

    if similarity_score >= 0.40:
        return "Orta"

    if similarity_score >= MINIMUM_SIMILARITY_SCORE:
        return "Düşük"

    return "Yetersiz"


# ==================================================
# DETAYLI CEVAP BULMA
# ==================================================

def find_answer_details(
    question: str,
    category: str
) -> dict[str, Any]:
    """
    Cevap, güven skoru, eşleşen soru ve öneri
    gibi bütün sonuçları sözlük olarak döndürür.
    """

    support_items = load_questions()

    normalized_category = str(
        category
    ).strip().lower()

    category_items = [
        item
        for item in support_items
        if str(
            item.get(
                "category",
                ""
            )
        ).strip().lower() == normalized_category
    ]

    normalized_question = normalize_text(
        question
    )

    if not normalized_question:

        return {
            "answer": (
                "Lütfen teknik sorununuzu daha ayrıntılı "
                "bir şekilde yazın."
            ),
            "confidence_score": 0,
            "confidence_level": "Yetersiz",
            "matched_question": None,
            "suggestion": None,
            "match_type": "empty"
        }

    if not category_items:

        return {
            "answer": (
                "Bu kategori için henüz kayıtlı bir çözüm "
                "bulunmuyor. Lütfen başka bir kategori seçin."
            ),
            "confidence_score": 0,
            "confidence_level": "Yetersiz",
            "matched_question": None,
            "suggestion": None,
            "match_type": "no_category_data"
        }

    exact_match = find_exact_match(
        question,
        category_items
    )

    if exact_match is not None:

        return {
            "answer": str(
                exact_match.get(
                    "answer",
                    ""
                )
            ),
            "confidence_score": 100,
            "confidence_level": "Yüksek",
            "matched_question": str(
                exact_match.get(
                    "question",
                    ""
                )
            ),
            "suggestion": None,
            "match_type": "exact"
        }

    keyword_item, keyword_score = find_keyword_match(
        question,
        category_items
    )

    best_item, hybrid_score = find_best_hybrid_match(
        question,
        category_items
    )

    # Anahtar kelime eşleşmesi çok güçlüyse
    # sonuç skoruna küçük bir katkı yapılır.
    if (
        keyword_item is not None
        and keyword_item == best_item
    ):

        final_score = min(
            1.0,
            hybrid_score
            + keyword_score * 0.15
        )

    else:

        final_score = hybrid_score

    confidence_percentage = (
        convert_score_to_percentage(
            final_score
        )
    )

    confidence_level = get_confidence_level(
        final_score
    )

    if (
        best_item is not None
        and final_score >= MINIMUM_SIMILARITY_SCORE
    ):

        return {
            "answer": str(
                best_item.get(
                    "answer",
                    ""
                )
            ),
            "confidence_score": confidence_percentage,
            "confidence_level": confidence_level,
            "matched_question": str(
                best_item.get(
                    "question",
                    ""
                )
            ),
            "suggestion": None,
            "match_type": "hybrid"
        }

    if (
        best_item is not None
        and final_score >= SUGGESTION_SIMILARITY_SCORE
    ):

        suggested_question = str(
            best_item.get(
                "question",
                ""
            )
        )

        return {
            "answer": (
                "Sorunuzla yeterince güçlü bir çözüm "
                "eşleşmesi bulunamadı. Lütfen sorununuzu "
                "biraz daha ayrıntılı yazın."
            ),
            "confidence_score": confidence_percentage,
            "confidence_level": "Yetersiz",
            "matched_question": None,
            "suggestion": suggested_question,
            "match_type": "suggestion"
        }

    return {
        "answer": (
            "Yazdığınız sorun seçtiğiniz kategoriyle "
            "yeterince eşleşmedi veya bilgi tabanımızda "
            "bu sorunla ilgili bir çözüm bulunmuyor. "
            "Lütfen sorunu daha ayrıntılı yazın."
        ),
        "confidence_score": confidence_percentage,
        "confidence_level": "Yetersiz",
        "matched_question": None,
        "suggestion": None,
        "match_type": "not_found"
    }


# ==================================================
# ESKİ APP.PY İLE UYUMLULUK
# ==================================================

def find_answer(
    question: str,
    category: str
) -> str:
    """
    Mevcut app.py dosyasının çalışmaya devam
    etmesi için yalnızca cevap metnini döndürür.
    """

    result = find_answer_details(
        question,
        category
    )

    return str(
        result.get(
            "answer",
            ""
        )
    )


# ==================================================
# KATEGORİYE GÖRE ÖRNEK SORULAR
# ==================================================

def get_questions_by_category(
    category: str
) -> list[str]:
    """
    Seçilen kategorideki örnek soruları
    alfabetik olarak döndürür.
    """

    support_items = load_questions()

    normalized_category = str(
        category
    ).strip().lower()

    questions = [
        str(
            item.get(
                "question",
                ""
            )
        )
        for item in support_items
        if (
            str(
                item.get(
                    "category",
                    ""
                )
            ).strip().lower()
            == normalized_category
            and item.get(
                "question"
            )
        )
    ]

    return sorted(
        questions,
        key=lambda question: normalize_text(
            question
        )
    )