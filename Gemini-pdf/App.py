import os
from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename
import PyPDF2
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
import traceback

GOOGLE_API_KEY = "AIzaSyDmtYUVOnB6QIje8cntEV36TIfnvy4IRyo"
EMAIL_REMETENTE = "jefersontorres006@gmail.com.br"
EMAIL_PASSWORD = "@Bank.av4578--"
EMAIL_DESTINATARIO = "silva.torres@hotmail.com"

# --- CONFIGURAÇÕES ---
UPLOAD_FOLDER = 'uploads_simples'
ALLOWED_EXTENSIONS = {'pdf'}
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MODEL_NAME = "gemini-2.0-flash"

genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- FUNÇÕES AUXILIARES ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ler_pdf(caminho_pdf):
    texto = ""
    try:
        with open(caminho_pdf, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            if leitor.is_encrypted:
                try: leitor.decrypt('')
                except: pass
            for pagina in leitor.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina: texto += texto_pagina + "\n"
        return texto if texto.strip() else None, None
    except Exception as e:
        return None, f"Erro ao ler o PDF: {e}"

def gerar_conclusao(texto_pdf, nome_arquivo):
    if not texto_pdf or texto_pdf.isspace():
        return None, "Texto do PDF está vazio."
    max_len = 30000
    texto_pdf = texto_pdf[:max_len]
    prompt = f"Com base no texto do documento '{nome_arquivo}', gere uma conclusão objetiva em português:\n\n---\n{texto_pdf}\n---\n\nConclusão:"
    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = model.generate_content(prompt)
        if not response.parts:
            reason = response.prompt_feedback.block_reason if response.prompt_feedback else "desconhecido"
            return None, f"Geração bloqueada. Motivo: {reason}"
        return response.text.strip(), None
    except Exception as e:
        return None, f"Erro na API Gemini: {e}"

def enviar_email(titulo, mensagem):
    if not mensagem.strip():
        mensagem = "(Não foi possível gerar a conclusão)"
    msg = EmailMessage()
    msg['Subject'] = f"Conclusão PDF: {titulo}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg.set_content(mensagem)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True, None
    except Exception as e:
        return False, f"Erro ao enviar email: {e}"

# --- ROTA PRINCIPAL ---
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = success_message = conclusao = filename = None

    if request.method == "POST":
        if "file" not in request.files or not request.files["file"].filename:
            error_message = "Nenhum arquivo selecionado."
        else:
            file = request.files["file"]
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(caminho_pdf)
                    texto_pdf, err_ler = ler_pdf(caminho_pdf)
                    if err_ler:
                        error_message = err_ler
                    else:
                        conclusao, err_gerar = gerar_conclusao(texto_pdf, filename)
                        if err_gerar:
                            error_message = err_gerar
                        else:
                            email_ok, err_email = enviar_email(filename, conclusao)
                            if email_ok:
                                success_message = f"✅ Conclusão gerada e enviada para {EMAIL_DESTINATARIO}!"
                            else:
                                error_message = f"Conclusão gerada, mas falha ao enviar email: {err_email}"
                except Exception as e:
                    error_message = f"Erro ao processar arquivo: {e}"
            else:
                error_message = "Tipo de arquivo inválido. Apenas PDFs são permitidos."

    # --- HTML COM BOOTSTRAP ---
    html_template = """
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <title>Conclusão PDF Simples</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="text-center mb-4">
                        <h1 class="fw-bold text-primary">Gerador de Conclusão de PDF</h1>
                        <p class="text-muted">Faça upload de um PDF para gerar uma conclusão automaticamente e enviá-la por email.</p>
                    </div>

                    {% if error_message %}
                        <div class="alert alert-danger">{{ error_message }}</div>
                    {% endif %}
                    {% if success_message %}
                        <div class="alert alert-success">{{ success_message }}</div>
                    {% endif %}

                    <div class="card shadow-sm">
                        <div class="card-body">
                            <form method="post" enctype="multipart/form-data" class="text-center">
                                <div class="mb-3">
                                    <label for="file" class="form-label fw-semibold">Selecione o arquivo PDF:</label>
                                    <input type="file" class="form-control" id="file" name="file" accept=".pdf" required>
                                </div>
                                <button type="submit" class="btn btn-primary px-4">Gerar e Enviar Conclusão</button>
                            </form>
                        </div>
                    </div>

                    {% if conclusao %}
                        <div class="card mt-5 shadow-sm">
                            <div class="card-header bg-success text-white fw-bold">
                                Conclusão Gerada para "{{ filename }}"
                            </div>
                            <div class="card-body">
                                <pre class="bg-light p-3 border rounded" style="white-space: pre-wrap;">{{ conclusao }}</pre>
                            </div>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    </body>
    </html>
    """

    return render_template_string(html_template,
                                  error_message=error_message,
                                  success_message=success_message,
                                  conclusao=conclusao,
                                  filename=filename)

# --- INICIAR SERVIDOR ---
if __name__ == "__main__":
    print("-" * 60)
    print("Iniciando servidor Flask...")
    print("Acesse em: http://localhost:5000")
    print("-" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
