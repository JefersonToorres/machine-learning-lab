import os
import pandas as pd
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import win32com.client

# --- CONFIGURAÇÕES ---
GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
MODEL_NAME = "gemini-2.0-flash"
EMAIL_DESTINATARIO = "torres.sillva@icloud.com"

MAX_TOKENS = 4000
TEMPERATURE = 0.0
TOP_P = 0.0
TOP_K = 1

# --- CONFIGURAÇÃO DA API ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# --- MÊS ATUAL ---
hoje = datetime.today()
mes_atual = hoje.month
ano_atual = hoje.year

# --- CAMINHO DA PLANILHA ---
arquivo_excel = r"C:\Users\silva\OneDrive\Documentos\Finance\Controladoria\Minhas Finanças.xlsm"

# === Função para enviar e-mail pelo Outlook ===
def enviar_email_outlook(assunto, corpo, destinatarios, anexo_path=None):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = assunto
        mail.Body = corpo
        mail.To = "; ".join(destinatarios if isinstance(destinatarios, list) else [destinatarios])

        if anexo_path:
            anexo_path = os.path.abspath(anexo_path)
            if os.path.exists(anexo_path):
                mail.Attachments.Add(anexo_path)
            else:
                raise FileNotFoundError(f"Anexo não encontrado: {anexo_path}")

        mail.Send()
        print("📧 E-mail enviado com sucesso via Outlook!")
    except Exception as e:
        raise Exception(f"Erro ao enviar e-mail via Outlook: {e}")

# === PROCESSAMENTO ===
try:
    planilhas = pd.read_excel(arquivo_excel, sheet_name=None)
    texto_planilhas = ""

    for nome_aba, df in planilhas.items():
        col_data = next((col for col in df.columns if 'data' in col.lower()), None)

        if col_data:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
            df = df[(df[col_data].dt.month == mes_atual) & (df[col_data].dt.year == ano_atual)]

        if not df.empty:
            texto_planilhas += f"\n\n---\n📄 Aba: {nome_aba} ({hoje.strftime('%B/%Y')})\n\n{df.to_string(index=False)}\n"

    if not texto_planilhas.strip():
        raise ValueError("Nenhum dado encontrado para o mês atual nas planilhas.")

    prompt = f"""
    Você é um analista financeiro e realizou a análise dos gastos de Jeferson Torres. Faça um resumo detalhado de como foi o mês{hoje.strftime('%B/%Y')}:

    {texto_planilhas}

    1. Identifique os maiores gastos e categorias.
    2. Aponte padrões ou comportamentos.
    """

    response = model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K
        }
    )

    resultado = response.text

    # === GERAÇÃO DO PDF BONITO ===
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Relatório Financeiro - {hoje.strftime('%B/%Y')}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for linha in resultado.split('\n'):
        if linha.strip().startswith("1.") or linha.strip().startswith("2.") or linha.strip().startswith("3.") or linha.strip().startswith("4.") or linha.strip().startswith("5."):
            pdf.set_font("Arial", 'B', 13)
        elif linha.strip().lower().startswith("resumo executivo"):
            pdf.set_font("Arial", 'B', 14)
            pdf.ln(5)
        elif linha.strip() == "":
            pdf.ln(4)
            continue
        else:
            pdf.set_font("Arial", size=12)

        pdf.multi_cell(0, 10, linha)

    caminho_pdf = "Relatorio_Financeiro_Mensal.pdf"
    pdf.output(caminho_pdf)

    # === ENVIO POR OUTLOOK ===
    enviar_email_outlook(
        assunto=f"Relatório Financeiro - {hoje.strftime('%B/%Y')}",
        corpo="Segue em anexo o relatório financeiro mensal gerado com IA.",
        destinatarios=[EMAIL_DESTINATARIO],
        anexo_path=caminho_pdf
    )

    print("✅ Relatório gerado e enviado com sucesso!")

except Exception as e:
    print(f"❌ Erro ao processar o relatório: {e}")
