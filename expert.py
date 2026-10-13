import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- Настройки ---
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY")  # Ключ будем хранить отдельно!

# Категории и количество вариантов (ПОДСТАВЬТЕ СВОИ ФАЙЛЫ)
CATEGORIES = {
    "Категория_1": 7,
    "Категория_2": 4,
    "Категория_3": 5,
    "Категория_4": 11,
}

# --- HTML страница (то, что увидит пользователь) ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Мой Агент</title></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 40px auto;">
  <h2>Задайте вопрос агенту</h2>
  <form id="agentForm">
    {% for cat, count in cats.items() %}
      <div style="margin-bottom: 10px;">
        <label>{{ cat }}: </label>
        <select id="{{ cat }}">
          {% for i in range(1, count + 1) %}
            <option value="{{ i }}">Вариант {{ i }}</option>
          {% endfor %}
        </select>
      </div>
    {% endfor %}
    <textarea id="question" rows="3" style="width:100%;" placeholder="Ваш вопрос..."></textarea>
    <br><br>
    <button type="button" onclick="askAgent()">Спросить</button>
  </form>
  <h3>Ответ:</h3>
  <pre id="answer" style="white-space: pre-wrap; background:#f4f4f4; padding:10px;"></pre>

  <script>
    async function askAgent() {
      document.getElementById('answer').textContent = 'Думаю...';
      const selections = {};
      {% for cat in cats %}
        selections['{{ cat }}'] = document.getElementById('{{ cat }}').value;
      {% endfor %}
      
      const response = await fetch('/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          question: document.getElementById('question').value,
          selections: selections
        })
      });
      const data = await response.json();
      document.getElementById('answer').textContent = data.answer || 'Ошибка: ' + (data.error || 'Неизвестно');
    }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE, cats=CATEGORIES)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    selections = data.get("selections", {})  # {"Категория_1": 3, ...}

    # Собираем текст из выбранных файлов
    context_parts = []
    for cat, num in selections.items():
        # Путь к файлу: data/Категория_1/Категория_1_3.txt (пример)
        filename = f"{cat}_{num}.txt"
        filepath = os.path.join("data", cat, filename)
        
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                context_parts.append(f"=== {cat}, Вариант {num} ===\n{f.read()}")
        else:
            context_parts.append(f"[Файл {filename} не найден]")
    
    context = "\n\n".join(context_parts)

    # Отправляем в OpenRouter
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/free",  # Автоматически выберет бесплатную модель
                "messages": [
                    {"role": "system", "content": "Ты ассистент. Отвечай только на основе документов. Если ответа нет — скажи об этом."},
                    {"role": "user", "content": f"Документы:\n{context}\n\nВопрос: {question}"}
                ]
            },
            timeout=60
        )
        result = response.json()
        return jsonify({"answer": result["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)