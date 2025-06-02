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
import numpy as np

# === CONFIGURAÇÕES ===
API_TOKEN_BRAPI = 'wd11P6ggfscs5UYkr6XB6t'
GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
load_dotenv()
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

# === DADOS DA SUA CARTEIRA (AJUSTE AQUI COM SEUS DADOS REAIS) ===
carteira_posicao = {
    'CPTR11': {'quantidade': 5, 'preco_medio': 95.50},
    'HGLG11': {'quantidade': 10, 'preco_medio': 95.60},
    'KNRI11': {'quantidade': 1, 'preco_medio': 100.10},
    'RECR11': {'quantidade': 1, 'preco_medio': 105.15},
    'JURO11': {'quantidade': 2, 'preco_medio': 102.12},
    'TRXF11': {'quantidade': 90, 'preco_medio': 102.80},   
    'HSML11': {'quantidade': 75, 'preco_medio': 125.60},   
    'KNSC11': {'quantidade': 110, 'preco_medio': 88.90},   
    'XPLG11': {'quantidade': 85, 'preco_medio': 98.75}     
}

# === DADOS DE DIVIDENDOS MENSAIS (%) - AJUSTE COM SEUS DADOS REAIS ===
dividendos_mensais = {
    'Janeiro': 0.65,
    'Fevereiro': 0.72,
    'Março': 0.68,
    'Abril': 0.75,
    'Maio': 0.69,
    'Junho': 0.71,
    # 'Julho': 0.73,
    # 'Agosto': 0.67,
    # 'Setembro': 0.70,
    # 'Outubro': 0.74,
    # 'Novembro': 0.66,
    # 'Dezembro': 0.78
}

fii_list = list(carteira_posicao.keys())
EMAIL_DESTINATARIOS = ['torres.sillva@icloud.com']

# === Função para enviar e-mail pelo SendGrid ===
def enviar_email_sendgrid(assunto, corpo_html, destinatarios, anexos_paths=None):
    message = Mail(
        from_email='torres.sillva@icloud.com',
        to_emails=destinatarios,
        subject=assunto,
        html_content=HtmlContent(corpo_html)
    )

    if anexos_paths:
        for anexo_path in anexos_paths:
            if os.path.exists(anexo_path):
                with open(anexo_path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment()
                    attachment.file_content = FileContent(encoded)
                    attachment.file_type = FileType('image/png')
                    attachment.file_name = FileName(os.path.basename(anexo_path))
                    attachment.disposition = Disposition('attachment')
                    if not message.attachment:
                        message.attachment = [attachment]
                    else:
                        message.attachment.append(attachment)

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
            preco_atual = info.get('regularMarketPrice', 0)
            quantidade = carteira_posicao[fii]['quantidade']
            preco_medio = carteira_posicao[fii]['preco_medio']
            
            valor_investido = quantidade * preco_medio
            valor_atual = quantidade * preco_atual
            ganho_perda = valor_atual - valor_investido
            ganho_perda_percent = (ganho_perda / valor_investido) * 100 if valor_investido > 0 else 0
            
            data.append({
                'FII': info.get('symbol', ''),
                'Nome': info.get('longName', ''),
                'Quantidade': quantidade,
                'Preço Médio': preco_medio,
                'Preço Atual': preco_atual,
                'Valor Investido': valor_investido,
                'Valor Atual': valor_atual,
                'Ganho/Perda (R$)': ganho_perda,
                'Ganho/Perda (%)': ganho_perda_percent,
                'Variação Diária (%)': info.get('regularMarketChangePercent', 0),
                'Volume': info.get('regularMarketVolume', 0),
                'Data': today
            })
    except Exception as e:
        print(f'❌ Erro ao buscar {fii}: {e}')

# === GERA GRÁFICOS E ENVIA EMAIL ===
df = pd.DataFrame(data)
if not df.empty:
    os.makedirs("relatorios", exist_ok=True)
    
    # Paths dos gráficos
    grafico_variacao_path = os.path.abspath(f"relatorios/variacao_fiis_{datetime.now().strftime('%Y%m%d')}.png")
    grafico_pizza_path = os.path.abspath(f"relatorios/pizza_carteira_{datetime.now().strftime('%Y%m%d')}.png")
    grafico_dividendos_path = os.path.abspath(f"relatorios/dividendos_mensais_{datetime.now().strftime('%Y%m%d')}.png")

    # === GRÁFICO 1: VARIAÇÃO DIÁRIA ===
    plt.figure(figsize=(12, 6))
    cores = ['green' if x > 0 else 'red' for x in df['Variação Diária (%)']]
    bars = plt.bar(df['FII'], df['Variação Diária (%)'], color=cores)

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
    plt.savefig(grafico_variacao_path, dpi=300, bbox_inches='tight')
    plt.close()

    # === GRÁFICO 2: PIZZA DA CARTEIRA ===
    plt.figure(figsize=(12, 8))
    
    # Calcular valores para o gráfico de pizza
    valores_atuais = df['Valor Atual'].values
    labels = [f"{row['FII']}\nR$ {row['Valor Atual']:,.0f}\n({row['Valor Atual']/df['Valor Atual'].sum()*100:.1f}%)" 
              for _, row in df.iterrows()]
    
    # Cores personalizadas
    cores_pizza = plt.cm.Set3(np.linspace(0, 1, len(df)))
    
    # Criar o gráfico de pizza
    wedges, texts, autotexts = plt.pie(valores_atuais, labels=labels, autopct='',
                                       colors=cores_pizza, startangle=90,
                                       textprops={'fontsize': 9})
    
    plt.title('🥧 Composição da Carteira de FIIs\n(Valores Atuais)', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Adicionar informações adicionais
    total_investido = df['Valor Investido'].sum()
    total_atual = df['Valor Atual'].sum()
    ganho_total = total_atual - total_investido
    ganho_percent = (ganho_total / total_investido) * 100
    
    plt.figtext(0.02, 0.02, f'Total Investido: R$ {total_investido:,.2f}\n'
                           f'Valor Atual: R$ {total_atual:,.2f}\n'
                           f'Ganho/Perda: R$ {ganho_total:,.2f} ({ganho_percent:+.2f}%)',
                fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
    
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(grafico_pizza_path, dpi=300, bbox_inches='tight')
    plt.close()

    # === GRÁFICO 3: DIVIDENDOS MENSAIS ===
    plt.figure(figsize=(12, 6))
    
    meses = list(dividendos_mensais.keys())
    percentuais = list(dividendos_mensais.values())
    
    # Criar gráfico de barras para dividendos
    bars = plt.bar(meses, percentuais, color='steelblue', alpha=0.8)
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.title('💰 Distribuição de Dividendos Mensais (%)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Mês', fontsize=12)
    plt.ylabel('Dividendo (%)', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Adicionar linha de média
    media_dividendos = np.mean(percentuais)
    plt.axhline(y=media_dividendos, color='red', linestyle='--', alpha=0.7, 
                label=f'Média: {media_dividendos:.2f}%')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(grafico_dividendos_path, dpi=300, bbox_inches='tight')
    plt.close()

    # === GERA ANÁLISE COM GEMINI ===
    prompt = f"""
    Você é um analista financeiro da Torres Capital. Com base nesses dados da carteira de FIIs:

    {df.to_string(index=False)}
    
    Total Investido: R$ {total_investido:,.2f}
    Valor Atual: R$ {total_atual:,.2f}
    Ganho/Perda Total: R$ {ganho_total:,.2f} ({ganho_percent:+.2f}%)
    
    Dividendos Mensais Médios: {np.mean(percentuais):.2f}%

    Gere um relatório completo e profissional sobre a carteira. Você é um gestor do fundo Torres Capital.
    
    Divida sua análise em 4 seções:
    1. Visão Geral da Carteira
    2. Performance Individual dos Ativos
    3. Análise de Dividendos
    4. Recomendações e Estratégias
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    resposta = model.generate_content(prompt)
    analise_texto = resposta.text.strip()

    # === CRIA TABELA HTML EXPANDIDA ===
    tabela_html = """
    <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-family: Arial, sans-serif; font-size: 12px;">
        <thead>
            <tr style="background-color: #003366; color: white;">
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">FII</th>
                <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Nome</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Qtd</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">P. Médio</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">P. Atual</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Valor Investido</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Valor Atual</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Ganho/Perda</th>
                <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Var. Diária</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in df.iterrows():
        cor_ganho = "#009900" if row['Ganho/Perda (%)'] > 0 else "#CC0000"
        cor_variacao = "#009900" if row['Variação Diária (%)'] > 0 else "#CC0000"
        
        tabela_html += f"""
            <tr>
                <td style="padding: 6px; text-align: left; border: 1px solid #ddd;">{row['FII']}</td>
                <td style="padding: 6px; text-align: left; border: 1px solid #ddd; font-size: 10px;">{row['Nome'][:25]}...</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd;">{row['Quantidade']}</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd;">R$ {row['Preço Médio']:.2f}</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd;">R$ {row['Preço Atual']:.2f}</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd;">R$ {row['Valor Investido']:,.0f}</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd;">R$ {row['Valor Atual']:,.0f}</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd; color: {cor_ganho};">{row['Ganho/Perda (%)']:+.2f}%</td>
                <td style="padding: 6px; text-align: right; border: 1px solid #ddd; color: {cor_variacao};">{row['Variação Diária (%)']:+.2f}%</td>
            </tr>
        """

    tabela_html += f"""
        </tbody>
        <tfoot>
            <tr style="background-color: #f0f0f0; font-weight: bold;">
                <td colspan="5" style="padding: 8px; text-align: right; border: 1px solid #ddd;">TOTAL:</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">R$ {total_investido:,.0f}</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">R$ {total_atual:,.0f}</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd; color: {'#009900' if ganho_percent > 0 else '#CC0000'};">{ganho_percent:+.2f}%</td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">-</td>
            </tr>
        </tfoot>
    </table>
    """

    # Formata a análise do Gemini em HTML
    analise_html = ""
    sections = analise_texto.split("\n\n")
    for section in sections:
        if section.strip():
            if any(heading in section.lower() for heading in ["visão geral", "performance", "dividendos", "recomendações"]):
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
        <title>Relatório Completo de FIIs - Torres Capital</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1000px; margin: 0 auto; padding: 20px;">
        
        <!-- Cabeçalho -->
        <div style="background-color: #003366; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
            <h1 style="margin: 0;">📊 Relatório Completo da Carteira de FIIs</h1>
            <p style="margin: 5px 0 0;">{today} | Torres Capital</p>
        </div>
        
        <!-- Resumo Executivo -->
        <div style="background-color: #f0f8ff; padding: 20px; border-left: 4px solid #003366; margin: 20px 0;">
            <h2 style="margin-top: 0; color: #003366;">📈 Resumo Executivo</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Total Investido</h3>
                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: #003366;">R$ {total_investido:,.2f}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Valor Atual</h3>
                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: #003366;">R$ {total_atual:,.2f}</p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Resultado</h3>
                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: {'#009900' if ganho_percent > 0 else '#CC0000'};">
                        {ganho_percent:+.2f}%
                    </p>
                </div>
                <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="margin: 0; color: #666;">Dividend Yield Médio</h3>
                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0; color: #003366;">{np.mean(percentuais):.2f}%</p>
                </div>
            </div>
        </div>
        
        <!-- Gráficos -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">📊 Análises Gráficas</h2>
        <p>Os gráficos em anexo apresentam:</p>
        <ul>
            <li><strong>Variação Diária:</strong> Performance de hoje de cada FII</li>
            <li><strong>Composição da Carteira:</strong> Distribuição dos investimentos</li>
            <li><strong>Dividendos Mensais:</strong> Histórico de distribuições</li>
        </ul>
        
        <!-- Tabela de Posições -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">📋 Posições Detalhadas</h2>
        {tabela_html}
        
        <!-- Análise do Mercado -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">🎯 Análise Profissional</h2>
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

    # === ENVIA EMAIL COM TODOS OS GRÁFICOS ===
    assunto = f'📊 Relatório Completo FIIs - Torres Capital ({today})'
    anexos = [grafico_variacao_path, grafico_pizza_path, grafico_dividendos_path]
    enviar_email_sendgrid(assunto, corpo_html, EMAIL_DESTINATARIOS, anexos_paths=anexos)

else:
    print("⚠️ Nenhum dado válido disponível.")