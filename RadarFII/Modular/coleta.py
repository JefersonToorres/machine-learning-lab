import requests
import pandas as pd
from config import FII_LIST, API_TOKEN_BRAPI, DATA_HOJE

def coletar_dados_fiis():
    dados = []
    for fii in FII_LIST:
        try:
            url = f'https://brapi.dev/api/quote/{fii}?token={API_TOKEN_BRAPI}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json().get('results', [])
            if result:
                info = result[0]
                dados.append({
                    'FII': info.get('symbol'),
                    'Nome': info.get('longName'),
                    'Preço Atual': info.get('regularMarketPrice', 0),
                    'Variação (%)': info.get('regularMarketChangePercent', 0),
                    'Volume': info.get('regularMarketVolume', 0),
                    'Data': DATA_HOJE
                })
        except Exception as e:
            print(f"❌ Erro ao buscar {fii}: {e}")
    return pd.DataFrame(dados)
