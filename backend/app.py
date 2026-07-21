from flask import Flask, render_template, request
from ai_engine import find_answer

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
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
    app.run(debug=True)