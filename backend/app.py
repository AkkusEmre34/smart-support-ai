from pathlib import Path

from flask import Flask, render_template, request
from ai_engine import find_answer


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = PROJECT_FOLDER / "frontend" / "templates"
STATIC_FOLDER = PROJECT_FOLDER / "frontend" / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_FOLDER),
    static_folder=str(STATIC_FOLDER)
)


@app.route("/", methods=["GET", "POST"])
def home():
    answer = None
    question = ""

    if request.method == "POST":
        question = request.form.get("question", "")
        answer = find_answer(question)

    return render_template(
        "index.html",
        answer=answer,
        question=question
    )


if __name__ == "__main__":
    print("HTML klasörü:", TEMPLATE_FOLDER)
    print("index.html var mı:", (TEMPLATE_FOLDER / "index.html").exists())
    app.run(debug=True)