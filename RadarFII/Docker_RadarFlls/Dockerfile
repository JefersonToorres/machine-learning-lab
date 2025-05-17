# Imagem base minimalista com Python
FROM python:3.11-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Garante que a pasta de relatórios exista
RUN mkdir -p /app/relatorios

# Expõe uma porta (não usada nesse script, mas útil se quiser rodar Flask futuramente)
EXPOSE 8080

# Comando padrão
CMD ["python", "relatorio_fiis.py"]
