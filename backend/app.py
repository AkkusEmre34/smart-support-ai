from pathlib import Path

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


@app.route("/", methods=["GET", "POST"])
def home():
    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        category = request.form.get("category", "").strip()

        if category not in CATEGORIES:
            category = "diger"

        if question:
            answer = find_answer(question, category)

            chat_history = session["chat_history"]

            chat_history.append(
                {
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "category_name": CATEGORIES[category]
                }
            )

            session["chat_history"] = chat_history

        return redirect(url_for("home"))

    category_questions = {
        category_key: get_questions_by_category(category_key)
        for category_key in CATEGORIES
    }

    return render_template(
        "index.html",
        chat_history=session["chat_history"],
        categories=CATEGORIES,
        category_questions=category_questions
    )


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