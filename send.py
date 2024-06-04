import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, message):
    sender_email = 'danielproemio@gmail.com'
    sender_password = 's m x c l bsxd t w p g l c q'
    receiver_email = 'stanybless@gmail.com'

    msg = MIMEMultipart()
    #msg = MIMEText(message)

    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print("Erro ao enviar e-mail:", e)
        
send_email("Atualização Concluída", "A atualização dos resultados foi concluída no Monitoramento.")
