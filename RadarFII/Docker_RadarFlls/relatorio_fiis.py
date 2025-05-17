import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from datetime import datetime
import google.generativeai as genai
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, HtmlContent
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
def enviar_email_sendgrid(assunto, corpo_html, destinatarios, anexo_path=None):
    message = Mail(
        from_email='torres.sillva@icloud.com',
        to_emails=destinatarios,
        subject=assunto,
        html_content=HtmlContent(corpo_html)
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
    
    Divida sua análise em 3 seções:
    1. Visão Geral do Mercado
    2. Destaques e Oportunidades
    3. Recomendações
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    resposta = model.generate_content(prompt)
    analise_texto = resposta.text.strip()

    # Cria tabela HTML com dados dos FIIs
    tabela_html = """
    <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-family: Arial, sans-serif; font-size: 14px;">
        <thead>
            <tr style="background-color: #003366; color: white;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">FII</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Nome</th>
                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Preço Atual</th>
                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Variação (%)</th>
                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Volume</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in df.iterrows():
        cor_variacao = "#009900" if row['Variação (%)'] > 0 else "#CC0000"
        tabela_html += f"""
            <tr>
                <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{row['FII']}</td>
                <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">{row['Nome']}</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">R$ {row['Preço Atual']:.2f}</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd; color: {cor_variacao};">{row['Variação (%)']:.2f}%</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">{row['Volume']:,.0f}</td>
            </tr>
        """

    tabela_html += """
        </tbody>
    </table>
    """

    # Formata a análise do Gemini em HTML
    analise_html = ""
    sections = analise_texto.split("\n\n")
    for section in sections:
        if section.strip():
            if any(heading in section.lower() for heading in ["visão geral", "destaques", "recomendações"]):
                analise_html += f"<h2 style='color: #003366; margin-top: 25px;'>{section}</h2>"
            else:
                analise_html += f"<p style='margin-bottom: 15px; line-height: 1.5;'>{section}</p>"

    # === ESTRUTURA DO EMAIL HTML ===
    corpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de FIIs - Torres Capital</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        
        <!-- Cabeçalho -->
        <div style="background-color: #003366; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
            <h1 style="margin: 0;">Relatório Diário de FIIs</h1>
            <p style="margin: 5px 0 0;">{today} | Torres Capital</p>
        </div>
        
        <!-- Introdução -->
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #003366; margin: 20px 0;">
            <p>Prezado(a) investidor(a),</p>
            <p>Apresentamos o relatório diário dos Fundos de Investimento Imobiliário da nossa carteira recomendada. Abaixo você encontrará os dados atualizados e uma análise completa do mercado.</p>
        </div>
        
        <!-- Resumo do Dia -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Resumo do Dia</h2>
        <p>O gráfico em anexo apresenta a variação diária dos FIIs monitorados pela Torres Capital.</p>
        
        <!-- Tabela de FIIs -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Dados Atualizados</h2>
        {tabela_html}
        
        <!-- Análise do Mercado -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Análise de Mercado</h2>
        {analise_html}
        
        <!-- Rodapé -->
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
            <p><strong>Torres Capital</strong> | Gestão Profissional de Investimentos</p>
            <p style="margin-top: 5px;">Este relatório tem caráter meramente informativo e não constitui oferta, solicitação de compra ou venda de valores mobiliários.</p>
            <p style="margin-top: 5px;">Para mais informações entre em contato pelo e-mail <a href="mailto:torres.sillva@icloud.com">torres.sillva@icloud.com</a></p>
        </div>
        
    </body>
    </html>
    """

    # === ENVIA EMAIL COM HTML ===
    assunto = f'📊 Relatório FIIs - Torres Capital ({today})'
    enviar_email_sendgrid(assunto, corpo_html, EMAIL_DESTINATARIOS, anexo_path=grafico_path)

else:
    print("⚠️ Nenhum dado válido disponível.")