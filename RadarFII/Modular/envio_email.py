from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, HtmlContent
import base64
import os
from config import SENDGRID_API_KEY, DATA_HOJE

def envio_email(assunto, corpo_html, destinatarios, anexo_path=None):
    message = Mail(
        from_email='torres.sillva@icloud.com',
        to_emails=destinatarios,
        subject=assunto,
        html_content=HtmlContent(corpo_html)
    )

    if anexo_path and os.path.exists(anexo_path):
        with open(anexo_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            attachment.file_type = FileType('image/png')
            attachment.file_name = FileName(os.path.basename(anexo_path))
            attachment.disposition = Disposition('attachment')
            message.attachment = attachment

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"📧 E-mail enviado com status {response.status_code} via SendGrid!")
    except Exception as e:
        raise Exception(f"Erro ao enviar e-mail: {e}")
