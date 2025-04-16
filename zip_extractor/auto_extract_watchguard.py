import os
import zipfile
import shutil
import win32com.client
from datetime import datetime

# ========== CONFIGURAÇÕES ==========
PASTA_DESTINO = r"C:\Report_Firewall\Reports"
PALAVRAS_PARA_DELETAR = ["Legacy-OnPremises_DLP_Summary", "Legacy-OnPremises_spamBlocker_Summary", "Legacy-OnPremises_HIPAA_Summary","Legacy-OnPremises_GAV_Summary","Legacy-OnPremises_Authentication_Allowed","Legacy-OnPremises_Authentication_Denied","Firebox-AZBR_","Legacy-OnPremises_Access_Portal_Summary","Legacy-OnPremises_APT_Summary","Legacy-OnPremises_Denied_Quota_Summary","Legacy-OnPremises_IMAP_Summary","Legacy-OnPremises_IPS_Summary","Legacy-OnPremises_POP3_Summary","Legacy-OnPremises_RED_Summary","Legacy-OnPremises_SMTP_Summary"]  # Adicione o que quiser aqui
REMETENTE = "cloud.watchguard.com"

# ========== INICIALIZAÇÃO ==========
outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
inbox = outlook.GetDefaultFolder(6)
messages = inbox.Items
messages.Sort("[ReceivedTime]", True)

# ========== CRIA A PASTA DESTINO ==========
if not os.path.exists(PASTA_DESTINO):
    os.makedirs(PASTA_DESTINO)

# ========== PROCESSA OS EMAILS ==========
for message in messages:
    if message.Class != 43:  # MailItem
        continue

    if REMETENTE in message.SenderEmailAddress:
        print(f"Processando e-mail: {message.Subject}")

        for attachment in message.Attachments:
            if attachment.FileName.lower().endswith(".zip"):
                zip_path = os.path.join(PASTA_DESTINO, attachment.FileName)
                attachment.SaveAsFile(zip_path)
                print(f"Salvo: {zip_path}")

                # Extração do ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(PASTA_DESTINO)
                    print(f"Extraído: {zip_path}")

                # Deleta o ZIP após extração
                os.remove(zip_path)

                # Deleta arquivos indesejados
                for nome_arquivo in os.listdir(PASTA_DESTINO):
                    for palavra in PALAVRAS_PARA_DELETAR:
                        if palavra.lower() in nome_arquivo.lower():
                            caminho = os.path.join(PASTA_DESTINO, nome_arquivo)
                            os.remove(caminho)
                            print(f"Removido: {caminho}")

        break  # Remove se quiser processar todos os e-mails do dia

print("Finalizado.")
