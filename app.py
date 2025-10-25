import gradio as gr
import os
import json
import fitz
import requests

# Завантаження мануалів з JSON
with open("manuals.json", "r", encoding="utf-8") as f:
    manuals = json.load(f)

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
    key_word = message.lower().split()[0]
    results = [m for m in manuals if key_word in [tag for tag in m["tags"]]]
    context = "Знайдені мануали:\n"
    for m in results:
        fragment = m["content"] if m["content"] else extract_pdf_fragment(m["file_path"])
        context += f"- [{m['title']}]({m['file_path']})\nФрагмент: {fragment}...\n"
    
    response = f"Запит: {message}\n{context}\nКроки дебагу: (NanoChat у розробці)"
    return response

demo = gr.ChatInterface(
    fn=chat_fn,
    title="FPV Debug Bot (Betaflight Focus)",
    description="Дебаг FPV-дронів: Betaflight, ESC, PID. Мануали з JSON."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8080)
