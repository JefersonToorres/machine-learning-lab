import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import google.generativeai as genai
import os

# === CONFIGURAÇÕES ===
API_TOKEN_BRAPI = 'wd11P6ggfscs5UYkr6XB6t'
GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
fii_list = ['CPTR11', 'HGLG11', 'KNRI11', 'RECR11', 'JURO11','TRXF11','HSML11','KNSC11','XPLG11']

# Configura o Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Data de hoje
today = datetime.now().strftime('%d/%m/%Y')

# Coleta os dados
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
        else:
            print(f'❌ Nenhum dado para {fii}')
    except Exception as e:
        print(f'❌ Erro ao buscar {fii}: {e}')

# Criação do DataFrame
df = pd.DataFrame(data)

if not df.empty and 'Variação (%)' in df.columns:
    # Gráfico
    plt.figure(figsize=(10, 5))
    cores = ['green' if x > 0 else 'red' for x in df['Variação (%)']]
    plt.bar(df['FII'], df['Variação (%)'], color=cores)
    plt.title('Variação Diária dos FIIs')
    plt.xlabel('FII')
    plt.ylabel('Variação (%)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('variacao_fiis.png')
    plt.show()

    # Geração da conclusão com Gemini
    prompt = f"""
    Você é um analista financeiro. Com base nesses dados:

    {df.to_string(index=False)}

    Gere um resumo do mercado de FIIs hoje. Destaque os fundos com maior e menor variação, volume negociado e qualquer tendência que se destaque.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    resposta = model.generate_content(prompt)

    print('\n📊 Conclusão do dia:')
    print(resposta.text)

    # Cria pasta "relatorios" se não existir
    os.makedirs("relatorios", exist_ok=True)

    # Salva a conclusão em um arquivo txt
    nome_arquivo = f'relatorios/conclusao_fiis_{datetime.now().strftime("%Y%m%d")}.txt'
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        f.write(f"Data: {today}\n")
        f.write("Conclusão do mercado de FIIs:\n\n")
        f.write(resposta.text)

    print(f'\n✅ Conclusão salva em: {nome_arquivo}')
else:
    print("⚠️ Nenhum dado válido disponível. Verifique o token ou a conexão.")
