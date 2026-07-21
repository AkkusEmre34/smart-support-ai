def normalize_text(text):
    return (
        text.strip()
        .lower()
        .replace("i̇", "i")
        .replace("ı", "i")
    )


def find_answer(question):
    question = normalize_text(question)

    if "internet" in question or "wifi" in question:
        return "Modemi yeniden başlatın ve Wi-Fi bağlantınızı kontrol edin."

    elif "bilgisayar acilmiyor" in question:
        return "Güç kablosunu, bataryayı ve güç düğmesini kontrol edin."

    elif "sifre" in question:
        return "Şifremi unuttum seçeneğini kullanarak şifrenizi yenileyin."

    else:
        return "Sorununuzu anlayamadım. Lütfen daha ayrıntılı açıklayın."