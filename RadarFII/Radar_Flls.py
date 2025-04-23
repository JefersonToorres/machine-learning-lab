import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from datetime import datetime
import google.generativeai as genai
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from dotenv import load_dotenv

# === CONFIGURAÇÕES ===
API_TOKEN_BRAPI = 'wd11P6ggfscs5UYkr6XB6t'
GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
load_dotenv()
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
fii_list = ['CPTR11', 'HGLG11', 'KNRI11', 'RECR11', 'JURO11','TRXF11','HSML11','KNSC11','XPLG11']
EMAIL_DESTINATARIOS = ['torres.sillva@icloud.com']

# === Função para enviar e-mail pelo SendGrid ===
def enviar_email_sendgrid(assunto, corpo, destinatarios, anexo_path=None):
    message = Mail(
        from_email='torres.sillva@icloud.com',
        to_emails=destinatarios,
        subject=assunto,
        plain_text_content=corpo
    )

    if anexo_path and os.path.exists(anexo_path):
        with open(anexo_path, 'rb') as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            attachment.file_type = FileType('image/png')
            attachment.file_name = FileName(os.path.basename(anexo_path))
            attachment.disposition = Disposition('attachment')
            message.attachment = attachment

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"📧 E-mail enviado com status {response.status_code} via SendGrid!")
    except Exception as e:
        raise Exception(f"Erro ao enviar e-mail via SendGrid: {e}")

# === CONFIGURA O GEMINI ===
genai.configure(api_key=GOOGLE_API_KEY)

# === DATA ===
today = datetime.now().strftime('%d/%m/%Y')

# === COLETA DADOS ===
data = []
for fii in fii_list:
    url = f'https://brapi.dev/api/quote/{fii}?token={API_TOKEN_BRAPI}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json().get('results')
        if result:
            info = result[0]
            data.append({
                'FII': info.get('symbol', ''),
                'Nome': info.get('longName', ''),
                'Preço Atual': info.get('regularMarketPrice', 0),
                'Variação (%)': info.get('regularMarketChangePercent', 0),
                'Volume': info.get('regularMarketVolume', 0),
                'Data': today
            })
    except Exception as e:
        print(f'❌ Erro ao buscar {fii}: {e}')

# === GERA GRÁFICO E ENVIA EMAIL ===
df = pd.DataFrame(data)
if not df.empty:
    os.makedirs("relatorios", exist_ok=True)
    grafico_path = os.path.abspath(f"relatorios/variacao_fiis_{datetime.now().strftime('%Y%m%d')}.png")

    # === GRÁFICO BONITO ===
    plt.figure(figsize=(12, 6))
    cores = ['green' if x > 0 else 'red' for x in df['Variação (%)']]
    bars = plt.bar(df['FII'], df['Variação (%)'], color=cores)

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + (0.1 if height >= 0 else -0.5),
            f"{height:.2f}%",
            ha='center',
            va='bottom' if height >= 0 else 'top',
            fontsize=9,
            fontweight='bold'
        )

    plt.title('📈 Variação Diária dos FIIs', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('FII', fontsize=12)
    plt.ylabel('Variação (%)', fontsize=12)
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.box(False)
    plt.tight_layout()
    plt.savefig(grafico_path)
    plt.close()

    # === GERA ANÁLISE COM GEMINI ===
    prompt = f"""
    Você é um analista financeiro. Com base nesses dados:

    {df.to_string(index=False)}

    Gere um relatório do mercado financeiro de hoje. Você é um gestor do fundo Torres Capital e deve fazer uma análise detalhada sobre como foi o dia dos seus ativos. Me fale sugestões de investimentos.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    resposta = model.generate_content(prompt)
    analise_texto = resposta.text.strip()

    # === ENVIA SOMENTE A IMAGEM POR EMAIL ===
    assunto = f'Relatório FIIs - {today}'
    corpo = (
        f'Olá,\n\n'
        f'Segue em anexo o gráfico com as variações diárias dos FIIs da Carteira.\n\n'
        f'Análise do dia:\n\n{analise_texto}\n\n'
        f'Atenciosamente,\nTorres Capital'
    )

    enviar_email_sendgrid(assunto, corpo, EMAIL_DESTINATARIOS, anexo_path=grafico_path)

else:
    print("⚠️ Nenhum dado válido disponível.")
