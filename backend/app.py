from collections import Counter
from pathlib import Path
from uuid import uuid4

from flask import Flask, redirect, render_template, request, session, url_for

from ai_engine import find_answer, get_questions_by_category


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = PROJECT_FOLDER / "frontend" / "templates"
STATIC_FOLDER = PROJECT_FOLDER / "frontend" / "static"

CATEGORIES = {
    "internet": "🌐 İnternet",
    "ses": "🔊 Ses",
    "yazici": "🖨️ Yazıcı",
    "mikrofon": "🎤 Mikrofon",
    "donanim": "🖥️ Donanım",
    "usb": "🔌 USB",
    "kamera": "📷 Kamera",
    "diger": "🛠️ Diğer"
}

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_FOLDER),
    static_folder=str(STATIC_FOLDER)
)

app.secret_key = "smart-support-ai-secret-key"


def prepare_chat_history():
    chat_history = session.get("chat_history", [])
    history_changed = False

    for chat in chat_history:
        if "id" not in chat:
            chat["id"] = str(uuid4())
            history_changed = True

        if "feedback" not in chat:
            chat["feedback"] = None
            history_changed = True

        if "category" not in chat:
            chat["category"] = "diger"
            history_changed = True

        if "category_name" not in chat:
            category = chat.get("category", "diger")
            chat["category_name"] = CATEGORIES.get(
                category,
                CATEGORIES["diger"]
            )
            history_changed = True

    if history_changed:
        session["chat_history"] = chat_history

    return chat_history


def calculate_statistics(chat_history):
    total_questions = len(chat_history)

    positive_feedback = sum(
        1
        for chat in chat_history
        if chat.get("feedback") == "positive"
    )

    negative_feedback = sum(
        1
        for chat in chat_history
        if chat.get("feedback") == "negative"
    )

    unanswered_feedback = sum(
        1
        for chat in chat_history
        if not chat.get("feedback")
    )

    category_counter = Counter(
        chat.get("category", "diger")
        for chat in chat_history
    )

    if category_counter:
        most_used_category_key, most_used_category_count = (
            category_counter.most_common(1)[0]
        )

        most_used_category_name = CATEGORIES.get(
            most_used_category_key,
            CATEGORIES["diger"]
        )
    else:
        most_used_category_name = "Henüz veri yok"
        most_used_category_count = 0

    category_statistics = []

    for category_key, category_name in CATEGORIES.items():
        category_statistics.append(
            {
                "key": category_key,
                "name": category_name,
                "count": category_counter.get(category_key, 0)
            }
        )

    return {
        "total_questions": total_questions,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "unanswered_feedback": unanswered_feedback,
        "most_used_category_name": most_used_category_name,
        "most_used_category_count": most_used_category_count,
        "category_statistics": category_statistics
    }


@app.route("/", methods=["GET", "POST"])
def home():
    chat_history = prepare_chat_history()

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        category = request.form.get("category", "").strip()

        if category not in CATEGORIES:
            category = "diger"

        if question:
            answer = find_answer(question, category)

            chat_history.append(
                {
                    "id": str(uuid4()),
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "category_name": CATEGORIES[category],
                    "feedback": None
                }
            )

            session["chat_history"] = chat_history

        return redirect(url_for("home"))

    category_questions = {
        category_key: get_questions_by_category(category_key)
        for category_key in CATEGORIES
    }

    statistics = calculate_statistics(chat_history)

    return render_template(
        "index.html",
        chat_history=chat_history,
        categories=CATEGORIES,
        category_questions=category_questions,
        statistics=statistics
    )


@app.route("/feedback/<chat_id>", methods=["POST"])
def save_feedback(chat_id):
    feedback = request.form.get("feedback", "").strip()

    if feedback not in ["positive", "negative"]:
        return redirect(url_for("home"))

    chat_history = prepare_chat_history()

    for chat in chat_history:
        if chat.get("id") == chat_id:
            chat["feedback"] = feedback
            break

    session["chat_history"] = chat_history

    return redirect(url_for("home") + f"#chat-{chat_id}")


@app.route("/clear-history", methods=["POST"])
def clear_history():
    session["chat_history"] = []
    return redirect(url_for("home"))


if __name__ == "__main__":
    print("HTML klasörü:", TEMPLATE_FOLDER)
    print(
        "index.html var mı:",
        (TEMPLATE_FOLDER / "index.html").exists()
    )

    app.run(debug=True)