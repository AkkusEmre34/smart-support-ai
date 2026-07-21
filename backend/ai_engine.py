import json
import re
from pathlib import Path
from typing import Any


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_FOLDER / "data" / "questions.json"


def normalize_text(text: str) -> str:
    text = text.lower().strip()

    replacements = {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c"
    }

    for old_character, new_character in replacements.items():
        text = text.replace(old_character, new_character)

    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def load_questions() -> list[dict[str, Any]]:
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        return data

    except FileNotFoundError:
        print(f"Veri dosyası bulunamadı: {DATA_FILE}")
        return []

    except json.JSONDecodeError as error:
        print(f"JSON dosyasında hata var: {error}")
        return []


def calculate_score(question: str, support_item: dict[str, Any]) -> int:
    normalized_question = normalize_text(question)

    support_question = normalize_text(
        str(support_item.get("question", ""))
    )

    keywords = support_item.get("keywords", [])

    score = 0

    if support_question == normalized_question:
        score += 100

    if support_question in normalized_question:
        score += 40

    for keyword in keywords:
        normalized_keyword = normalize_text(str(keyword))

        if normalized_keyword in normalized_question:
            score += 20

        keyword_words = normalized_keyword.split()
        question_words = normalized_question.split()

        for word in keyword_words:
            if word in question_words and len(word) > 2:
                score += 3

    return score


def find_answer(question: str, category: str) -> str:
    support_items = load_questions()

    category_items = [
        item
        for item in support_items
        if item.get("category") == category
    ]

    if not category_items:
        return (
            "Bu kategori için henüz kayıtlı bir çözüm bulunmuyor. "
            "Lütfen başka bir kategori seçin."
        )

    best_item = None
    best_score = 0

    for item in category_items:
        current_score = calculate_score(question, item)

        if current_score > best_score:
            best_score = current_score
            best_item = item

    if best_item is not None and best_score >= 6:
        return str(best_item.get("answer", ""))

    return (
        "Yazdığınız soru seçtiğiniz kategoriyle eşleşmedi veya "
        "bilgi tabanımızda henüz bu sorunla ilgili yeterli çözüm bulunmuyor. "
        "Lütfen kategoriyi kontrol ederek sorunu daha ayrıntılı yazın."
    )


def get_questions_by_category(category: str) -> list[str]:
    support_items = load_questions()

    return [
        str(item.get("question", ""))
        for item in support_items
        if item.get("category") == category
        and item.get("question")
    ]