import json
from pathlib import Path


def normalize_text(text):
    return (
        text.strip()
        .lower()
        .replace("i̇", "i")
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ç", "c")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
    )


def load_questions():
    file_path = Path(__file__).parent.parent / "data" / "questions.json"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        print("Hata: questions.json dosyası bulunamadı.")
        return []

    except json.JSONDecodeError:
        print("Hata: questions.json dosyasının yapısı bozuk.")
        return []


def find_answer(question):
    normalized_question = normalize_text(question)
    questions = load_questions()

    for item in questions:
        saved_question = normalize_text(item["question"])

        if (
            saved_question in normalized_question
            or normalized_question in saved_question
        ):
            return item["answer"]

    return "Sorununuzu anlayamadım. Lütfen daha ayrıntılı açıklayın."