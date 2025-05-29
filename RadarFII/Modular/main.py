from coleta import coletar_dados_fiis
from grafico import gerar_grafico_variacao
from analise import gerar_analise
from envio_email import envio_email
from config import EMAIL_DESTINATARIOS, DATA_HOJE

def montar_corpo_html(df, analise, grafico_nome="Relatório Diário de FIIs"):
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
    tabela_html += "</tbody></table>"

    # Análise em HTML
    analise_html = ""
    for bloco in analise.split("\n\n"):
        if bloco.strip():
            if any(sub in bloco.lower() for sub in ["visão geral", "destaques", "recomendações"]):
                analise_html += f"<h2 style='color: #003366; margin-top: 25px;'>{bloco}</h2>"
            else:
                analise_html += f"<p style='margin-bottom: 15px; line-height: 1.5;'>{bloco}</p>"

    # Corpo completo
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{grafico_nome}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        
        <!-- Cabeçalho -->
        <div style="background-color: #003366; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
            <h1 style="margin: 0;">{grafico_nome}</h1>
            <p style="margin: 5px 0 0;">{DATA_HOJE} | Torres Capital</p>
        </div>
        
        <!-- Introdução -->
        <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #003366; margin: 20px 0;">
            <p>Prezado(a) investidor(a),</p>
            <p>Apresentamos o relatório diário dos Fundos de Investimento Imobiliário da nossa carteira recomendada. Abaixo você encontrará os dados atualizados e uma análise completa do mercado.</p>
        </div>
        
        <!-- Resumo do Dia -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Resumo do Dia</h2>
        <p>O gráfico em anexo apresenta a variação diária dos FIIs monitorados pela Torres Capital.</p>
        
        <!-- Tabela -->
        <h2 style="color: #003366; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Dados Atualizados</h2>
        {tabela_html}
        
        <!-- Análise -->
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

def main():
    df = coletar_dados_fiis()
    if df.empty:
        print("⚠️ Nenhum dado coletado.")
        return

    grafico_path = gerar_grafico_variacao(df)
    analise_texto = gerar_analise(df)
    corpo_html = montar_corpo_html(df, analise_texto)
    envio_email(f'📊 Relatório FIIs - Torres Capital ({DATA_HOJE})', corpo_html, EMAIL_DESTINATARIOS, grafico_path)

if __name__ == "__main__":
    main()
