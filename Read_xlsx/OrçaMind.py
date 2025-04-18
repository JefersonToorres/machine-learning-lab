import pandas as pd
import google.generativeai as genai
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
from datetime import datetime
import matplotlib.pyplot as plt

# --- CONFIGURAÇÕES ---
GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
EMAIL_REMETENTE = "jefersontorres006@gmail.com.br"
EMAIL_PASSWORD = ""  # senha de app do Gmail
EMAIL_DESTINATARIO = "silva.torres@hotmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
MODEL_NAME = "gemini-2.0-flash"

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

try:
    planilhas = pd.read_excel(arquivo_excel, sheet_name=None)
    texto_planilhas = ""
    grafico_gerado = False

    for nome_aba, df in planilhas.items():
        col_data = next((col for col in df.columns if 'data' in col.lower()), None)

        if col_data:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
            df = df[(df[col_data].dt.month == mes_atual) & (df[col_data].dt.year == ano_atual)]

        if not df.empty:
            texto_planilhas += f"\n\n---\n**Aba: {nome_aba} (Filtrado por {hoje.strftime('%B/%Y')})**\n\n{df.to_string(index=False)}\n"

            # Tenta gerar gráfico se tiver colunas de valor e categoria
            col_valor = next((col for col in df.columns if 'valor' in col.lower() or 'total' in col.lower()), None)
            col_categoria = next((col for col in df.columns if 'categoria' in col.lower() or 'descrição' in col.lower()), None)

            if col_valor and col_categoria and not grafico_gerado:
                df_graf = df[[col_categoria, col_valor]].groupby(col_categoria).sum().sort_values(by=col_valor, ascending=False)
                plt.figure(figsize=(8, 5))
                df_graf.plot(kind='bar', legend=False)
                plt.title(f"Gastos por Categoria - {hoje.strftime('%B/%Y')}")
                plt.xlabel("Categoria")
                plt.ylabel("Total R$")
                plt.tight_layout()
                plt.savefig("grafico_gastos.png")
                plt.close()
                grafico_gerado = True

    if texto_planilhas.strip() == "":
        raise ValueError("Nenhum dado encontrado para o mês atual nas planilhas.")

    # Criar prompt
    prompt = f"""
    Você é um analista financeiro. Faça um relatório elaborado. Abaixo estão os dados filtrados da planilha financeira para o mês de {hoje.strftime('%B/%Y')}:

    {texto_planilhas}

    Com base nessas informações, por favor:
    1. Identifique os maiores gastos e em quais categorias eles ocorrem.
    2. Aponte possíveis padrões ou comportamentos de despesas.
    3. Avalie a saúde financeira com base nos dados apresentados.
    4. Sugira ao menos 3 ações para melhorar o desempenho financeiro.
    5. Gere um resumo executivo.

    Seja claro e direto.
    """

    # Gerar resposta com Gemini
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

    # Criar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for linha in resultado.split('\n'):
        pdf.multi_cell(0, 10, linha)

    # Adiciona gráfico se tiver sido gerado
    if grafico_gerado:
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(0, 10, "Gráfico de Gastos por Categoria", ln=True)
        pdf.image("grafico_gastos.png", x=10, y=30, w=190)

    caminho_pdf = "Relatorio_Financeiro_Mensal.pdf"
    pdf.output(caminho_pdf)

    # Enviar e-mail
    msg = EmailMessage()
    msg['Subject'] = f'Relatório Financeiro - {hoje.strftime("%B/%Y")}'
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg.set_content("Segue em anexo o relatório financeiro do mês gerado com IA.")

    with open(caminho_pdf, "rb") as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename="Relatorio_Financeiro_Mensal.pdf")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
        server.send_message(msg)

    print("✅ Relatório com gráfico gerado e enviado com sucesso!")

except Exception as e:
    print(f"❌ Erro ao processar o relatório: {e}")
