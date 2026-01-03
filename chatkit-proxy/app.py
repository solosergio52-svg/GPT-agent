from flask import Flask, Response, request
import requests

app = Flask(__name__)

CHATKIT_URL = "https://chat.openai.com/static/chat.js"

@app.route("/chatkit.js")
def chatkit_proxy():
    """Проксирует ChatKit-скрипт из OpenAI"""
    try:
        headers = {"User-Agent": request.headers.get("User-Agent")}
        r = requests.get(CHATKIT_URL, headers=headers, timeout=10)
        return Response(r.content, mimetype="application/javascript")
    except Exception as e:
        return Response(f"// Ошибка: {e}", mimetype="application/javascript")

@app.route("/")
def index():
    """Тестовая страница"""
    return """
    <html>
      <head><meta charset='UTF-8'><title>Buildeco Chat</title></head>
      <body style='height:100vh;display:flex;align-items:center;justify-content:center;'>
        <script src='/chatkit.js'
          data-workflow='wf_695907dc48308190b1541b47d9b71a0e0c3ff92ed5dbce97'
          data-version='2'
          data-theme='light'>
        </script>
      </body>
    </html>
    """
