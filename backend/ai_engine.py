import json
import re
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_FOLDER / "data" / "questions.json"

MINIMUM_SIMILARITY_SCORE = 0.12


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


def load_questions() -> list[dict[str, Any]]:
    """
    questions.json dosyasındaki teknik destek kayıtlarını yükler.
    """

    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            print(
                "questions.json içeriği liste biçiminde değil."
            )
            return []

        valid_items = []

        for item in data:
            if not isinstance(item, dict):
                continue

            category = str(
                item.get("category", "")
            ).strip()

            question = str(
                item.get("question", "")
            ).strip()

            answer = str(
                item.get("answer", "")
            ).strip()

            keywords = item.get("keywords", [])

            if not isinstance(keywords, list):
                keywords = []

            if not category or not question or not answer:
                continue

            valid_items.append(
                {
                    "category": category,
                    "question": question,
                    "keywords": keywords,
                    "answer": answer
                }
            )

        return valid_items

    except FileNotFoundError:
        print(
            f"Veri dosyası bulunamadı: {DATA_FILE}"
        )
        return []

    except json.JSONDecodeError as error:
        print(
            f"questions.json dosyasında JSON hatası var: {error}"
        )
        return []

    except OSError as error:
        print(
            f"questions.json okunurken hata oluştu: {error}"
        )
        return []


def create_search_text(
    support_item: dict[str, Any]
) -> str:
    """
    Bir destek kaydındaki soru ve anahtar kelimeleri
    tek bir metin hâline getirir.
    """

    question = str(
        support_item.get("question", "")
    )

    keywords = support_item.get(
        "keywords",
        []
    )

    if not isinstance(keywords, list):
        keywords = []

    keyword_text = " ".join(
        str(keyword)
        for keyword in keywords
    )

    combined_text = (
        f"{question} {keyword_text} {keyword_text}"
    )

    return normalize_text(combined_text)


def find_exact_keyword_match(
    question: str,
    category_items: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Kullanıcının yazdığı soru, kayıtlı soru veya anahtar
    kelimelerle doğrudan eşleşiyorsa ilgili kaydı döndürür.
    """

    normalized_question = normalize_text(question)

    for item in category_items:
        item_question = normalize_text(
            str(item.get("question", ""))
        )

        if normalized_question == item_question:
            return item

        keywords = item.get(
            "keywords",
            []
        )

        if not isinstance(keywords, list):
            continue

        for keyword in keywords:
            normalized_keyword = normalize_text(
                str(keyword)
            )

            if (
                normalized_keyword
                and normalized_keyword in normalized_question
            ):
                return item

    return None


def find_best_tfidf_match(
    question: str,
    category_items: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, float]:
    """
    TF-IDF ve cosine similarity kullanarak kullanıcının
    sorusuna en çok benzeyen teknik destek kaydını bulur.
    """

    if not category_items:
        return None, 0.0

    normalized_question = normalize_text(question)

    support_texts = [
        create_search_text(item)
        for item in category_items
    ]

    all_texts = support_texts + [
        normalized_question
    ]

    try:
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            lowercase=False,
            sublinear_tf=True
        )

        tfidf_matrix = vectorizer.fit_transform(
            all_texts
        )

    except ValueError:
        return None, 0.0

    question_vector = tfidf_matrix[-1]

    support_vectors = tfidf_matrix[:-1]

    similarity_scores = cosine_similarity(
        question_vector,
        support_vectors
    ).flatten()

    if similarity_scores.size == 0:
        return None, 0.0

    best_match_index = int(
        similarity_scores.argmax()
    )

    best_similarity_score = float(
        similarity_scores[best_match_index]
    )

    return (
        category_items[best_match_index],
        best_similarity_score
    )


def find_answer(
    question: str,
    category: str
) -> str:
    """
    Kullanıcının sorusuna uygun teknik destek cevabını bulur.
    """

    support_items = load_questions()

    normalized_category = str(
        category
    ).strip().lower()

    category_items = [
        item
        for item in support_items
        if str(
            item.get("category", "")
        ).strip().lower() == normalized_category
    ]

    if not category_items:
        return (
            "Bu kategori için henüz kayıtlı bir çözüm bulunmuyor. "
            "Lütfen başka bir kategori seçin."
        )

    normalized_question = normalize_text(
        question
    )

    if not normalized_question:
        return (
            "Lütfen teknik sorununuzu daha ayrıntılı bir şekilde yazın."
        )

    exact_match = find_exact_keyword_match(
        question,
        category_items
    )

    if exact_match is not None:
        return str(
            exact_match.get("answer", "")
        )

    best_item, similarity_score = find_best_tfidf_match(
        question,
        category_items
    )

    if (
        best_item is not None
        and similarity_score >= MINIMUM_SIMILARITY_SCORE
    ):
        return str(
            best_item.get("answer", "")
        )

    return (
        "Yazdığınız sorun seçtiğiniz kategoriyle yeterince eşleşmedi "
        "veya bilgi tabanımızda bu sorunla ilgili bir çözüm bulunmuyor. "
        "Lütfen sorunu daha ayrıntılı yazın."
    )


def get_questions_by_category(
    category: str
) -> list[str]:
    """
    Seçilen kategorideki örnek soruları döndürür.
    """

    support_items = load_questions()

    normalized_category = str(
        category
    ).strip().lower()

    return [
        str(item.get("question", ""))
        for item in support_items
        if (
            str(
                item.get("category", "")
            ).strip().lower() == normalized_category
            and item.get("question")
        )
    ]