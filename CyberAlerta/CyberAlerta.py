import os
import time
import feedparser
import openai
import datetime
import pytz
import requests
from dateutil import tz
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fuso
SAO_PAULO = pytz.timezone("America/Sao_Paulo")

# Feeds que serão lidos
FEEDS = [
    "https://www.windowslatest.com/feed/",
    "https://www.windowscentral.com/feed",
    "https://blogs.windows.com/feed/",
    "https://azure.microsoft.com/en-us/blog/feed/",
    "https://azurecrazy.com/feed/",
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://aws.amazon.com/blogs/feed/",
    "https://www.lastweekinaws.com/feed/",
    "https://mspoweruser.com/category/news/feed/",
    "https://www.pcmag.com/rss/feeds/windows.rss"
]

def get_yesterday_date():
    now_sp = datetime.datetime.now(SAO_PAULO)
    return (now_sp - datetime.timedelta(days=1)).date()

def fetch_reports(yesterday):
    reports = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if not hasattr(entry, "published_parsed"):
                continue
            dt = datetime.datetime.fromtimestamp(
                time.mktime(entry.published_parsed),
                tz=tz.tzutc()
            ).astimezone(SAO_PAULO)
            if dt.date() == yesterday:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                reports.append(f"- <b>{title}</b>\n  {link}\n")
    return reports

def summarize_reports(reports, yesterday):
    if not reports:
        return f"Não há novos relatos de problemas de cibersegurança relacionados a Azure/M365 em {yesterday:%d/%m/%Y}."

    prompt = (
        f"Resuma em texto corrido os problemas de cibersegurança reportados em {yesterday:%d/%m/%Y} "
        "relacionados a Microsoft Azure e Microsoft 365, com base nestes itens:\n\n"
        + "".join(reports) +
        "\nDestaque os que parecem mais críticos e dê recomendações gerais."
    )

    resp = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Você é um analista de cibersegurança especializado."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.1,
        top_p=1.0
    )
    return resp.choices[0].message.content.strip()

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    resp = requests.post(url, data=payload)
    resp.raise_for_status()

def main():
    yesterday = get_yesterday_date()
    reports = fetch_reports(yesterday)
    summary = summarize_reports(reports, yesterday)
    header = f"<b>Resumo de Cibersegurança</b>\n<em>{yesterday:%d/%m/%Y}</em>\n\n"
    send_telegram(header + summary)
    print("Resumo enviado com sucesso!")

if __name__ == "__main__":
    main()
