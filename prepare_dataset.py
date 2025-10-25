import psycopg2
import json
import os

# Supabase credentials (заміни на твої)
DATABASE_URL = os.getenv("DATABASE_URL")  # Або встав повний URI

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("SELECT title, file_path, content, tags FROM pdf_manuals")
results = cursor.fetchall()

# Створи пари запит-відповідь для SFT
dataset = []
for title, file_path, content, tags in results:
    for tag in tags:
        query = f"Дебаг {tag} у FPV-дроні"  # Приклад запитів
        response = f"З мануалу '{title}': {content[:200]}... Посилання: {file_path}. Кроки: 1. Перевірте ESC. 2. Оновіть прошивку."
        dataset.append({"query": query, "response": response})

with open("fpv_sft_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"Датасет готовий: {len(dataset)} прикладів")
