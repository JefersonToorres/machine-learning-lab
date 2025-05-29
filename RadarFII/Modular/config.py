import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# === CHAVES DE API E DADOS FIXOS ===
API_TOKEN_BRAPI = 'wd11P6ggfscs5UYkr6XB6t'
GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_DESTINATARIOS = ['torres.sillva@icloud.com']

# === LISTA DE FIIs E DATA ===
FII_LIST = ['CPTR11', 'HGLG11', 'KNRI11', 'RECR11', 'JURO11','TRXF11','HSML11','KNSC11','XPLG11']
DATA_HOJE = datetime.now().strftime('%d/%m/%Y')
