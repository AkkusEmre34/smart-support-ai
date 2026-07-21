from ai_engine import find_answer

print("Smart Support AI")
print("Çıkmak için 'çıkış' yazın.")

while True:
    question = input("\nSorununuzu yazın: ")

    if question.lower() == "çıkış":
        print("Program kapatıldı.")
        break

    answer = find_answer(question)
    print("Cevap:", answer)