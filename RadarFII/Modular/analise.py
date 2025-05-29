import google.generativeai as genai
from config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

def gerar_analise(df):
    prompt = f"""
    Você é um analista financeiro. Com base nesses dados:

    {df.to_string(index=False)}

    Gere um relatório do mercado financeiro de hoje dividido em:
    1. Visão Geral do Mercado
    2. Destaques e Oportunidades
    3. Recomendações
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    resposta = model.generate_content(prompt)
    return resposta.text.strip()
