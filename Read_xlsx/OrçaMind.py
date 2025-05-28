import os
import pandas as pd
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import win32com.client
import locale

# Configurar localização para português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass

class RelatorioFinanceiro:
    def __init__(self):
        # Configurações principais
        self.GOOGLE_API_KEY = "AIzaSyBAzeGLTtDWhl3L-GHc7KshqWaGa5_MyG4"
        self.MODEL_NAME = "gemini-2.0-flash"
        self.EMAIL_DESTINATARIO = "torres.sillva@icloud.com"
        self.arquivo_excel = r"C:\Users\silva\OneDrive\Documentos\Finance\Controladoria\Minhas Finanças.xlsm"
        
        # Configuração da API
        genai.configure(api_key=self.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(self.MODEL_NAME)
        
        # Data atual
        self.hoje = datetime.today()
        self.mes_atual = self.hoje.month
        self.ano_atual = self.hoje.year
        self.mes_nome = self.hoje.strftime('%B').capitalize()
        
    def processar_dados_mensais(self, mes_especifico=None, ano_especifico=None):
        """Processa dados do Excel filtrando por mês/ano específico ou atual"""
        try:
            mes_busca = mes_especifico or self.mes_atual
            ano_busca = ano_especifico or self.ano_atual
            
            print(f"🔍 Buscando dados para {mes_busca:02d}/{ano_busca}")
            
            planilhas = pd.read_excel(self.arquivo_excel, sheet_name=None)
            dados_organizados = {}
            info_debug = {}
            
            for nome_aba, df in planilhas.items():
                print(f"   📋 Analisando aba: {nome_aba}")
                
                if df.empty:
                    print(f"      ⚠️  Aba vazia")
                    continue
                
                # Encontrar todas as colunas que podem conter datas
                colunas_data = [col for col in df.columns if any(palavra in col.lower() 
                               for palavra in ['data', 'date', 'vencimento', 'pagamento'])]
                
                print(f"      📅 Colunas de data encontradas: {colunas_data}")
                
                if not colunas_data:
                    # Se não há coluna de data, incluir todos os dados
                    print(f"      ➕ Sem coluna de data - incluindo todos os dados")
                    dados_organizados[nome_aba] = df
                    info_debug[nome_aba] = {"total_linhas": len(df), "filtradas": len(df), "sem_data": True}
                    continue
                
                # Usar a primeira coluna de data encontrada
                col_data = colunas_data[0]
                df_copy = df.copy()
                
                # Converter para datetime
                df_copy[col_data] = pd.to_datetime(df_copy[col_data], errors='coerce')
                
                # Remover linhas com datas inválidas
                df_copy = df_copy.dropna(subset=[col_data])
                
                if df_copy.empty:
                    print(f"      ⚠️  Nenhuma data válida encontrada")
                    continue
                
                # Mostrar período de dados disponíveis
                data_min = df_copy[col_data].min()
                data_max = df_copy[col_data].max()
                print(f"      📊 Período dos dados: {data_min.strftime('%m/%Y')} a {data_max.strftime('%m/%Y')}")
                
                # Filtrar por mês e ano
                df_filtrado = df_copy[(df_copy[col_data].dt.month == mes_busca) & 
                                    (df_copy[col_data].dt.year == ano_busca)]
                
                total_linhas = len(df_copy)
                linhas_filtradas = len(df_filtrado)
                
                print(f"      📈 Total de registros: {total_linhas}")
                print(f"      🎯 Registros do período: {linhas_filtradas}")
                
                if not df_filtrado.empty:
                    dados_organizados[nome_aba] = df_filtrado
                
                info_debug[nome_aba] = {
                    "total_linhas": total_linhas,
                    "filtradas": linhas_filtradas,
                    "periodo": f"{data_min.strftime('%m/%Y')} - {data_max.strftime('%m/%Y')}",
                    "coluna_data": col_data
                }
            
            # Relatório de debug
            print(f"\n📋 RESUMO DO PROCESSAMENTO:")
            for aba, info in info_debug.items():
                if info.get("sem_data"):
                    print(f"   {aba}: {info['total_linhas']} registros (sem filtro de data)")
                else:
                    print(f"   {aba}: {info['filtradas']}/{info['total_linhas']} registros ({info['periodo']})")
            
            return dados_organizados, info_debug
            
        except Exception as e:
            raise Exception(f"Erro ao processar planilhas: {e}")
    
    def gerar_analise_ia(self, dados_organizados):
        """Gera análise financeira usando IA"""
        texto_dados = ""
        
        for nome_aba, df in dados_organizados.items():
            texto_dados += f"\n--- {nome_aba.upper()} ---\n"
            texto_dados += df.to_string(index=False)
            texto_dados += "\n"
        
        prompt = f"""
        Como analista financeiro especializado, analise os dados financeiros de {self.mes_nome}/{self.ano_atual} de Jeferson Torres.

        DADOS FINANCEIROS:
        {texto_dados}

        Forneça uma análise estruturada seguindo EXATAMENTE este formato:

        **RESUMO EXECUTIVO**
        [Visão geral do mês em 2-3 frases]

        **RECEITAS DO MÊS**
        [Análise das receitas identificadas]

        **PRINCIPAIS GASTOS**
        [Liste os 5 maiores gastos do mês com valores]

        **ANÁLISE POR CATEGORIA**
        [Agrupe gastos por categoria e analise]

        **COMPORTAMENTO FINANCEIRO**
        [Identifique padrões, tendências e comportamentos]

        **RECOMENDAÇÕES**
        [3-5 recomendações práticas para otimização]

        **COMPARATIVO E METAS**
        [Sugestões para próximos meses]

        Use linguagem clara, profissional e inclua valores específicos sempre que possível.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 4000,
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            return response.text
        except Exception as e:
            raise Exception(f"Erro na análise IA: {e}")
    
    def criar_pdf_profissional(self, analise):
        """Cria PDF com design profissional"""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Cabeçalho principal
        pdf.set_fill_color(41, 128, 185)  # Azul profissional
        pdf.rect(0, 0, 210, 40, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 20)
        pdf.ln(15)
        pdf.cell(0, 10, f"RELATÓRIO FINANCEIRO", ln=True, align='C')
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, f"{self.mes_nome.upper()} {self.ano_atual}", ln=True, align='C')
        
        # Linha separadora
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.set_draw_color(41, 128, 185)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(10)
        
        # Informações do relatório
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Gerado em: {self.hoje.strftime('%d/%m/%Y às %H:%M')}", ln=True)
        pdf.cell(0, 5, f"Beneficiário: Jeferson Torres", ln=True)
        pdf.ln(8)
        
        # Conteúdo da análise
        pdf.set_text_color(0, 0, 0)
        
        linhas = analise.split('\n')
        for linha in linhas:
            linha = linha.strip()
            
            if not linha:
                pdf.ln(3)
                continue
                
            # Títulos principais
            if linha.startswith('**') and linha.endswith('**'):
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 14)
                pdf.set_text_color(41, 128, 185)
                titulo = linha.replace('**', '')
                pdf.cell(0, 8, titulo, ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(2)
                continue
            
            # Subtítulos
            elif linha.startswith('•') or linha.startswith('-'):
                pdf.set_font("Arial", size=11)
                pdf.cell(0, 6, linha, ln=True)
                continue
            
            # Texto normal
            else:
                pdf.set_font("Arial", size=11)
                # Quebrar linhas longas
                if len(linha) > 80:
                    pdf.multi_cell(0, 6, linha)
                else:
                    pdf.cell(0, 6, linha, ln=True)
        
        # Rodapé
        pdf.ln(10)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("Arial", 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "Relatório gerado automaticamente por IA - Sistema de Controle Financeiro", 
                ln=True, align='C')
        
        caminho_pdf = f"Relatorio_Financeiro_{self.mes_nome}_{self.ano_atual}.pdf"
        pdf.output(caminho_pdf)
        return caminho_pdf
    
    def enviar_email_profissional(self, caminho_pdf, analise):
        """Envia email com formato profissional"""
        try:
            # Extrair resumo executivo para o corpo do email
            linhas = analise.split('\n')
            resumo = ""
            capturando_resumo = False
            
            for linha in linhas:
                if '**RESUMO EXECUTIVO**' in linha:
                    capturando_resumo = True
                    continue
                elif linha.startswith('**') and capturando_resumo:
                    break
                elif capturando_resumo and linha.strip():
                    resumo += linha + " "
            
            corpo_email = f"""
Olá Jeferson,

Segue o relatório financeiro referente ao mês de {self.mes_nome}/{self.ano_atual}.

RESUMO EXECUTIVO:
{resumo.strip()}

O relatório completo com análises detalhadas, recomendações e comparativos está em anexo.

---
Principais destaques do mês:
• Análise detalhada de receitas e despesas
• Identificação dos maiores gastos por categoria
• Padrões de comportamento financeiro
• Recomendações personalizadas para otimização
• Sugestões para os próximos meses

Para dúvidas ou esclarecimentos sobre o relatório, entre em contato.

Atenciosamente,
Sistema Automatizado de Controle Financeiro
Gerado em {self.hoje.strftime('%d/%m/%Y às %H:%M')}
            """
            
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.Subject = f"📊 Relatório Financeiro - {self.mes_nome}/{self.ano_atual}"
            mail.Body = corpo_email
            mail.To = self.EMAIL_DESTINATARIO
            
            # Anexar PDF
            caminho_absoluto = os.path.abspath(caminho_pdf)
            if os.path.exists(caminho_absoluto):
                mail.Attachments.Add(caminho_absoluto)
            else:
                raise FileNotFoundError(f"PDF não encontrado: {caminho_absoluto}")
            
            mail.Send()
            print(f"📧 Email enviado com sucesso para {self.EMAIL_DESTINATARIO}")
            
        except Exception as e:
            raise Exception(f"Erro ao enviar email: {e}")
    
    def sugerir_periodos_disponiveis(self, info_debug):
        """Sugere períodos com dados disponíveis"""
        periodos_disponiveis = set()
        
        for aba, info in info_debug.items():
            if not info.get("sem_data") and info['total_linhas'] > 0:
                periodo = info.get('periodo', '')
                if ' - ' in periodo:
                    inicio, fim = periodo.split(' - ')
                    periodos_disponiveis.add(inicio)
                    periodos_disponiveis.add(fim)
        
        if periodos_disponiveis:
            periodos_ordenados = sorted(list(periodos_disponiveis))
            print(f"\n💡 PERÍODOS COM DADOS DISPONÍVEIS:")
            for periodo in periodos_ordenados:
                print(f"   📅 {periodo}")
            
            # Sugerir o período mais recente
            if periodos_ordenados:
                ultimo_periodo = periodos_ordenados[-1]
                mes_num, ano_num = ultimo_periodo.split('/')
                print(f"\n🎯 SUGESTÃO: Execute o relatório para {ultimo_periodo}")
                print(f"   Para isso, modifique o método executar_relatorio_completo() para:")
                print(f"   relatorio.executar_relatorio_completo(mes_especifico={int(mes_num)}, ano_especifico={int(ano_num)})")
    
    def executar_relatorio_completo(self, mes_especifico=None, ano_especifico=None):
        """Executa o processo completo de geração do relatório"""
        mes_relatorio = mes_especifico or self.mes_atual
        ano_relatorio = ano_especifico or self.ano_atual
        nome_mes = datetime(ano_relatorio, mes_relatorio, 1).strftime('%B').capitalize()
        
        print(f"🔄 Iniciando geração do relatório para {nome_mes}/{ano_relatorio}...")
        
        try:
            # 1. Processar dados
            print("📊 Processando dados financeiros...")
            dados, info_debug = self.processar_dados_mensais(mes_especifico, ano_especifico)
            
            if not dados:
                print(f"\n❌ Nenhum dado encontrado para {nome_mes}/{ano_relatorio}")
                self.sugerir_periodos_disponiveis(info_debug)
                return False
            
            print(f"✅ Dados processados: {len(dados)} planilhas com dados encontradas")
            
            # Atualizar variáveis para o período específico
            self.mes_atual = mes_relatorio
            self.ano_atual = ano_relatorio
            self.mes_nome = nome_mes
            
            # 2. Gerar análise
            print("🤖 Gerando análise com IA...")
            analise = self.gerar_analise_ia(dados)
            print("✅ Análise gerada com sucesso")
            
            # 3. Criar PDF
            print("📄 Criando PDF profissional...")
            caminho_pdf = self.criar_pdf_profissional(analise)
            print(f"✅ PDF criado: {caminho_pdf}")
            
            # 4. Enviar email
            print("📧 Enviando relatório por email...")
            self.enviar_email_profissional(caminho_pdf, analise)
            
            print(f"🎉 Relatório de {nome_mes}/{ano_relatorio} gerado e enviado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro no processo: {e}")
            raise

# Execução principal
if __name__ == "__main__":
    relatorio = RelatorioFinanceiro()
    
    # Primeira tentativa com mês atual
    sucesso = relatorio.executar_relatorio_completo()
    
    # Se não encontrou dados, tenta com mês anterior
    if not sucesso:
        print(f"\n🔄 Tentando mês anterior...")
        mes_anterior = relatorio.hoje.month - 1 if relatorio.hoje.month > 1 else 12
        ano_anterior = relatorio.hoje.year if relatorio.hoje.month > 1 else relatorio.hoje.year - 1
        
        relatorio.executar_relatorio_completo(mes_anterior, ano_anterior)