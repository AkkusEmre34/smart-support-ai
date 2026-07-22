import json
from collections import Counter
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

from ai_engine import (
    find_answer,
    get_questions_by_category,
    load_questions
)

from database import (
    add_chat,
    clear_all_chats,
    get_all_chats,
    init_database,
    update_feedback
)


PROJECT_FOLDER = Path(__file__).resolve().parent.parent

TEMPLATE_FOLDER = PROJECT_FOLDER / "frontend" / "templates"
STATIC_FOLDER = PROJECT_FOLDER / "frontend" / "static"
QUESTIONS_FILE = PROJECT_FOLDER / "data" / "questions.json"


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

app.secret_key = "smart-support-ai-gizli-anahtar"

init_database()


def save_questions(support_items):
    """
    Bilgi tabanı kayıtlarını questions.json dosyasına kaydeder.
    """

    try:
        QUESTIONS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with QUESTIONS_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                support_items,
                file,
                ensure_ascii=False,
                indent=4
            )

        return True

    except OSError as error:
        print(
            "Bilgi tabanı kaydedilirken hata oluştu:",
            error
        )

        return False


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
        (
            most_used_category_key,
            most_used_category_count
        ) = category_counter.most_common(1)[0]

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
                "count": category_counter.get(
                    category_key,
                    0
                )
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
    if request.method == "POST":
        question = request.form.get(
            "question",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        if category not in CATEGORIES:
            category = "diger"

        if question:
            answer = find_answer(
                question,
                category
            )

            chat_id = str(uuid4())

            add_chat(
                chat_id=chat_id,
                question=question,
                answer=answer,
                category=category,
                category_name=CATEGORIES[category]
            )

        return redirect(
            url_for("home")
        )

    chat_history = get_all_chats()

    category_questions = {
        category_key: get_questions_by_category(
            category_key
        )
        for category_key in CATEGORIES
    }

    statistics = calculate_statistics(
        chat_history
    )

    return render_template(
        "index.html",
        chat_history=chat_history,
        categories=CATEGORIES,
        category_questions=category_questions,
        statistics=statistics
    )


@app.route("/admin")
def admin_panel():
    support_items = load_questions()

    return render_template(
        "admin.html",
        support_items=support_items,
        categories=CATEGORIES,
        total_items=len(support_items)
    )


@app.route("/admin/add", methods=["POST"])
def add_support_item():
    category = request.form.get(
        "category",
        ""
    ).strip()

    question = request.form.get(
        "question",
        ""
    ).strip()

    keywords_text = request.form.get(
        "keywords",
        ""
    ).strip()

    answer = request.form.get(
        "answer",
        ""
    ).strip()

    if category not in CATEGORIES:
        flash(
            "Lütfen geçerli bir kategori seçin.",
            "error"
        )

        return redirect(
            url_for("admin_panel")
        )

    if not question:
        flash(
            "Soru alanı boş bırakılamaz.",
            "error"
        )

        return redirect(
            url_for("admin_panel")
        )

    if not answer:
        flash(
            "Cevap alanı boş bırakılamaz.",
            "error"
        )

        return redirect(
            url_for("admin_panel")
        )

    keywords = [
        keyword.strip()
        for keyword in keywords_text.split(",")
        if keyword.strip()
    ]

    if not keywords:
        keywords = [question]

    support_items = load_questions()

    question_lower = question.lower()

    duplicate_question = any(
        str(
            item.get("question", "")
        ).strip().lower() == question_lower
        for item in support_items
    )

    if duplicate_question:
        flash(
            "Bu soru bilgi tabanında zaten bulunuyor.",
            "error"
        )

        return redirect(
            url_for("admin_panel")
        )

    new_support_item = {
        "category": category,
        "question": question,
        "keywords": keywords,
        "answer": answer
    }

    support_items.append(
        new_support_item
    )

    if not save_questions(support_items):
        flash(
            "Kayıt eklenirken bir hata oluştu.",
            "error"
        )

        return redirect(
            url_for("admin_panel")
        )

    flash(
        "Yeni teknik destek sorusu başarıyla eklendi.",
        "success"
    )

    return redirect(
        url_for("admin_panel")
    )


@app.route(
    "/feedback/<chat_id>",
    methods=["POST"]
)
def save_feedback(chat_id):
    feedback = request.form.get(
        "feedback",
        ""
    ).strip()

    if feedback not in [
        "positive",
        "negative"
    ]:
        return redirect(
            url_for("home")
        )

    update_feedback(
        chat_id,
        feedback
    )

    return redirect(
        url_for("home")
        + "#chat-"
        + chat_id
    )


@app.route(
    "/clear-history",
    methods=["POST"]
)
def clear_history():
    clear_all_chats()

    return redirect(
        url_for("home")
    )


if __name__ == "__main__":
    print(
        "HTML klasörü:",
        TEMPLATE_FOLDER
    )

    print(
        "index.html var mı:",
        (
            TEMPLATE_FOLDER
            / "index.html"
        ).exists()
    )

    print(
        "admin.html var mı:",
        (
            TEMPLATE_FOLDER
            / "admin.html"
        ).exists()
    )

    print(
        "Veritabanı hazır:",
        (
            PROJECT_FOLDER
            / "data"
            / "smart_support.db"
        ).exists()
    )

    app.run(
        debug=True
    )