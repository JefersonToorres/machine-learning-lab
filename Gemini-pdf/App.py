import os
from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename
import PyPDF2
import google.generativeai as genai
import smtplib
from email.message import EmailMessage
import traceback # Para mostrar erros mais detalhados se necessário

# --- Configurações e Credenciais (COLOCADAS DIRETAMENTE) ---

# !!! ATENÇÃO: MÉTODO INSEGURO PARA APLICAÇÕES REAIS !!!
GOOGLE_API_KEY = "AIzaSyDmtYUVOnB6QIje8cntEV36TIfnvy4IRyo"
EMAIL_REMETENTE = "jefersontorres006@gmail.com"
# IMPORTANTE: Se usa verificação em duas etapas no Gmail, GERE e use uma "Senha de App"
EMAIL_PASSWORD = "@Bank.av4578--" # SUA SENHA ou SENHA DE APP AQUI
EMAIL_DESTINATARIO = "silva.torres@hotmail.com"
# --- FIM DAS CREDENCIAIS ---

# --- Configurações Fixas ---
UPLOAD_FOLDER = 'uploads_simples' # Pasta para guardar os PDFs temporariamente
ALLOWED_EXTENSIONS = {'pdf'}
SMTP_SERVER = "smtp.gmail.com" # Servidor para Gmail
SMTP_PORT = 587
# --- MODELO GEMINI ATUALIZADO ---
MODEL_NAME = "gemini-1.5-flash-latest" # <--- MODELO ATUALIZADO (gemini-2.0-flash não é um nome padrão, use 1.5-flash-latest ou gemini-1.0-pro)

# --- Configurar API Google Gemini ---
try:
    # Usa a variável GOOGLE_API_KEY definida acima
    genai.configure(api_key=GOOGLE_API_KEY)
    print("API Google Gemini configurada com sucesso.")
except Exception as e:
    print(f"ERRO GRAVE: Falha ao configurar a API do Google Gemini: {e}")
    # Considerar parar a aplicação aqui se a API é essencial
    # exit()

# --- Inicializar Flask ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Garante que a pasta exista

# --- Funções Auxiliares (sem alterações na lógica interna) ---
def allowed_file(filename):
    """Verifica se a extensão do arquivo é PDF."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ler_pdf(caminho_pdf):
    """Extrai texto de um arquivo PDF."""
    texto = ""
    try:
        with open(caminho_pdf, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            if leitor.is_encrypted:
                try: leitor.decrypt('')
                except Exception: print(f"Aviso: PDF '{os.path.basename(caminho_pdf)}' encriptado.")

            for i, pagina in enumerate(leitor.pages):
                try:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina: texto += texto_pagina + "\n"
                except Exception as e: print(f"Erro ao extrair texto da página {i+1} do PDF '{os.path.basename(caminho_pdf)}': {e}")
        if not texto: return None, f"Não foi possível extrair texto do PDF '{os.path.basename(caminho_pdf)}'."
        return texto, None
    except FileNotFoundError: return None, f"Erro interno: Arquivo PDF não encontrado em {caminho_pdf}"
    except PyPDF2.errors.PdfReadError as e: return None, f"Erro ao ler o PDF '{os.path.basename(caminho_pdf)}': {e}"
    except Exception as e:
        print(f"Erro inesperado ao ler PDF: {traceback.format_exc()}")
        return None, f"Erro inesperado ao processar o PDF: {e}"

def gerar_conclusao(texto_pdf, nome_arquivo):
    """Gera uma conclusão usando a API Gemini."""
    if not texto_pdf or texto_pdf.isspace(): return None, "Texto do PDF está vazio."

    max_len = 30000
    if len(texto_pdf) > max_len:
        print(f"Aviso: Texto do PDF muito longo ({len(texto_pdf)} caracteres), usando os primeiros {max_len}.")
        texto_pdf = texto_pdf[:max_len]

    prompt = f"Com base no seguinte texto extraído do documento '{nome_arquivo}', gere uma conclusão objetiva e concisa em português:\n\n---\n{texto_pdf}\n---\n\nConclusão:"

    try:
        # Usa a variável MODEL_NAME definida acima
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = model.generate_content(prompt)

        if not response.parts:
             reason = response.prompt_feedback.block_reason if response.prompt_feedback else "desconhecido"
             return None, f"Geração bloqueada pela API. Motivo: {reason}"

        return response.text.strip(), None
    except Exception as e:
        print(f"Erro ao chamar a API Gemini: {traceback.format_exc()}")
        error_message = f"Erro na API Gemini: {e}"
        # Mensagens de erro específicas
        if hasattr(e, 'message'): # Verifica se o erro tem um atributo 'message'
             if "API key not valid" in e.message: error_message = "Erro: Chave da API do Google Gemini inválida."
             elif "404" in e.message and "models/" in e.message: error_message = f"Erro: Modelo Gemini '{MODEL_NAME}' não encontrado ou indisponível ({e})."
             elif "429" in e.message or "Resource has been exhausted" in e.message: error_message = "Erro: Limite de uso da API Gemini atingido. Tente mais tarde."
             elif "permission denied" in e.message.lower(): error_message = f"Erro: Permissão negada para usar o modelo '{MODEL_NAME}' com esta API Key."
        return None, error_message


def enviar_email(titulo, mensagem):
    """Envia a conclusão por email usando Gmail."""
    if not mensagem or mensagem.isspace():
        mensagem = "(Não foi possível gerar a conclusão ou ocorreu um erro)"

    msg = EmailMessage()
    msg['Subject'] = f"Conclusão PDF: {titulo}"
    # --- USA AS VARIÁVEIS DEFINIDAS NO TOPO ---
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg.set_content(mensagem)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            # --- USA AS VARIÁVEIS DEFINIDAS NO TOPO ---
            smtp.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email enviado com sucesso para {EMAIL_DESTINATARIO}")
        return True, None
    except smtplib.SMTPAuthenticationError:
        err_msg = "Erro de autenticação ao enviar email. Verifique seu EMAIL REMETENTE e SENHA (ou Senha de App)."
        print(err_msg)
        return False, err_msg
    except Exception as e:
        print(f"Erro ao enviar email: {traceback.format_exc()}")
        return False, f"Erro ao enviar email: {e}"

# --- Rota Principal do Flask ---
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None
    success_message = None
    conclusao = None
    filename = None

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
                    print(f"Arquivo salvo: {caminho_pdf}")
                    texto_pdf, err_ler = ler_pdf(caminho_pdf)
                    if err_ler: error_message = err_ler
                    else:
                        conclusao, err_gerar = gerar_conclusao(texto_pdf, filename)
                        if err_gerar: error_message = err_gerar
                        else:
                            email_ok, err_email = enviar_email(filename, conclusao)
                            if email_ok: success_message = f"✅ Conclusão gerada para '{filename}' e enviada para {EMAIL_DESTINATARIO}!"
                            else: error_message = f"Conclusão gerada, mas FALHA ao enviar email: {err_email}"
                except Exception as e:
                    print(f"Erro GERAL no processamento: {traceback.format_exc()}")
                    error_message = f"Ocorreu um erro inesperado: {e}"
                # finally: # Bloco de limpeza (opcional)
                #    if os.path.exists(caminho_pdf):
                #        try: os.remove(caminho_pdf); print(f"Arquivo removido: {caminho_pdf}")
                #        except OSError as e: print(f"Erro ao remover {caminho_pdf}: {e}")
            else: error_message = "Tipo de arquivo inválido. Apenas PDFs são permitidos."

    # --- HTML Simples (embutido) ---
    html_template = """
    <!doctype html>
    <html>
    <head>
        <title>Conclusão PDF Simples</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1, h2 { text-align: center; color: #333; }
            .message { padding: 12px; margin-bottom: 15px; border-radius: 4px; text-align: center; border: 1px solid transparent; }
            .error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
            .success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
            form { margin-bottom: 25px; padding: 20px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; text-align: center; }
            label { margin-right: 10px; font-weight: bold; }
            input[type=file] { border: 1px solid #ced4da; padding: 5px; border-radius: 4px; }
            button { padding: 10px 20px; cursor: pointer; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 1em; }
            button:hover { background-color: #0056b3; }
            pre { background-color: #e9ecef; padding: 15px; border: 1px solid #ced4da; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-size: 0.95em; line-height: 1.6; }
            hr { margin-top: 30px; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <h1>Gerador de Conclusão de PDF</h1>

        {% if error_message %} <div class="message error"><strong>Erro:</strong> {{ error_message }}</div> {% endif %}
        {% if success_message %} <div class="message success">{{ success_message }}</div> {% endif %}

        <form method="post" enctype="multipart/form-data">
            <label for="file">Selecione o arquivo PDF:</label>
            <input type="file" id="file" name="file" accept=".pdf" required>
            <button type="submit">Gerar e Enviar Conclusão</button>
        </form>

        {% if conclusao %}
            <hr>
            <h2>Conclusão Gerada para "{{ filename }}":</h2>
            <pre>{{ conclusao }}</pre>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html_template,
                                error_message=error_message,
                                success_message=success_message,
                                conclusao=conclusao,
                                filename=filename)

# --- Executar a Aplicação ---
if __name__ == "__main__":
    print("-" * 60)
    print("Iniciando servidor Flask (Modo Simples)...")
    print(f"   - Pasta de Uploads:   '{os.path.abspath(UPLOAD_FOLDER)}'")
    print(f"   - Modelo Gemini:      '{MODEL_NAME}'")
    # Mostra os emails que serão usados (definidos no topo do script)
    print(f"   - Email Remetente:    '{EMAIL_REMETENTE}'")
    print(f"   - Email Destinatário: '{EMAIL_DESTINATARIO}'")
    print("\n" + "="*20 + " ATENÇÃO: SEGURANÇA " + "="*20)
    print("   Credenciais (API Key, Senha de Email) estão no código fonte.")
    print("   Este método é INSEGURO para produção ou código compartilhado.")
    print("=" * (42 + len(" ATENÇÃO: SEGURANÇA ")))
    print("-" * 60)
    # Executa o servidor Flask, acessível na rede local (0.0.0.0)
    # debug=False é mais seguro que True
    app.run(host='0.0.0.0', port=5000, debug=False)