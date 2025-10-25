import gradio as gr
import psycopg2
import os
import fitz
import requests
import deepl

# DeepL
translator = deepl.Translator(os.getenv("DEEPL_API_KEY", ""))

# NanoChat
try:
    from nanochat_master.model import NanoGPT as NanoChatModel  # Використовуй NanoGPT з model.py
    model = NanoChatModel(vocab_size=50257, block_size=32, n_embd=64, n_head=4, n_layer=2)  # Ініціалізуй модель
    # Якщо є чекпоінт, завантаж: model.load_state_dict(torch.load("model.pth"))
    model.eval()
except Exception as e:
    print(f"NanoChat import error: {e}")
    model = None

# Supabase
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port="5432"
)
cursor = conn.cursor()

def extract_pdf_fragment(file_path):
    try:
        pdf_data = requests.get(file_path).content
        with open("temp.pdf", "wb") as f:
            f.write(pdf_data)
        doc = fitz.open("temp.pdf")
        text = "".join(page.get_text() for page in doc)[:300]
        doc.close()
        return text
    except:
        return "Фрагмент недоступний"

def chat_fn(message, history):
    lang = 'uk' if any(c in message.lower() for c in 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя') else 'en'
    target_lang = 'en' if lang == 'uk' else 'uk'
    
    query = "SELECT title, file_path, content, tags FROM pdf_manuals WHERE tags @> ARRAY[%s]::varchar[]"
    cursor.execute(query, (message.lower().split()[0],))
    results = cursor.fetchall()
    context = "Знайдені мануали:\n"
    for title, file_path, content, tags in results:
        fragment = content if content else extract_pdf_fragment(file_path)
        if ('ua' in tags and lang == 'en') or ('en' in tags and lang == 'uk'):
            try:
                fragment = translator.translate_text(fragment, target_lang=target_lang).text
            except:
                pass
        context += f"- [{title}]({file_path})\nФрагмент: {fragment}...\n"
    
    if model:
        prompt = f"Користувач: {message}\nКонтекст: {context}\nВідповідь: Чіткі кроки дебагу FPV мовою {lang}."
        # Генерація (адаптуй для NanoGPT)
        response = model.generate(prompt, max_length=500)  # Додай метод generate в model.py, якщо немає
    else:
        response = f"Запит: {message}\n{context}\nКроки дебагу: (NanoChat у розробці)"
    return response

demo = gr.ChatInterface(
    fn=chat_fn,
    title="FPV Debug Bot (Betaflight Focus)",
    description="Дебаг FPV-дронів: Betaflight, ESC, PID. Мануали з Supabase."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8080)
