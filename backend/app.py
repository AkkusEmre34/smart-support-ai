from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

from ai_engine import find_answer


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = PROJECT_FOLDER / "frontend" / "templates"
STATIC_FOLDER = PROJECT_FOLDER / "frontend" / "static"

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

        if question:
            answer = find_answer(question)

            chat_history = session["chat_history"]

            chat_history.append(
                {
                    "question": question,
                    "answer": answer
                }
            )

            session["chat_history"] = chat_history

        return redirect(url_for("home"))

    return render_template(
        "index.html",
        chat_history=session["chat_history"]
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