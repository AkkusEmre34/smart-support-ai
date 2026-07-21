import json
from pathlib import Path
from difflib import SequenceMatcher


GENERIC_WORDS = {
    "çalışmıyor",
    "çalışmiyor",
    "sorun",
    "hata",
    "bilgisayar",
    "cihaz",
    "olmuyor",
    "alamıyorum",
    "alamiyorum"
}


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
        .replace(".", "")
        .replace(",", "")
        .replace("?", "")
        .replace("!", "")
    )


def load_questions():
    file_path = Path(__file__).parent.parent / "data" / "questions.json"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            print("Hata: questions.json liste şeklinde olmalıdır.")
            return []

        return data

    except FileNotFoundError:
        print("Hata: questions.json dosyası bulunamadı.")
        return []

    except json.JSONDecodeError:
        print("Hata: questions.json dosyasının yapısı bozuk.")
        return []


def calculate_similarity(first_text, second_text):
    return SequenceMatcher(
        None,
        first_text,
        second_text
    ).ratio()


def find_answer(question):
    normalized_question = normalize_text(question)
    question_words = set(normalized_question.split())
    questions = load_questions()

    best_answer = None
    highest_score = 0

    for item in questions:
        saved_question = normalize_text(
            item.get("question", "")
        )

        keywords = item.get("keywords", [])
        score = 0

        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)

            if normalized_keyword in {
                normalize_text(word) for word in GENERIC_WORDS
            }:
                continue

            if normalized_keyword in normalized_question:
                score += 3

            elif any(
                calculate_similarity(normalized_keyword, word) >= 0.85
                for word in question_words
            ):
                score += 1

        sentence_similarity = calculate_similarity(
            normalized_question,
            saved_question
        )

        score += sentence_similarity

        if saved_question == normalized_question:
            score += 5

        if score > highest_score:
            highest_score = score
            best_answer = item.get("answer")

    if highest_score >= 2:
        return best_answer

    return (
        "Sorununuzu anlayamadım. "
        "Lütfen cihazı ve yaşadığınız sorunu daha ayrıntılı açıklayın."
    )