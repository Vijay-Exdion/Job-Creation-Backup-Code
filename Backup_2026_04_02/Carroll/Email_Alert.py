

##########################################################   FOR ONLY TEXT   ##############################################################

# from configparser import ConfigParser
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import os

# BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\carroll"

# def send_email(subject, body):

#     config = ConfigParser()
#     config.read(os.path.join(BASE_FOLDER, "Config.ini"))

#     sender = config.get("Email", "SENDER")
#     password = config.get("Email", "PASSWORD")
#     receiver = config.get("Email", "RECEIVER")

#     msg = MIMEMultipart()
#     msg["From"] = sender
#     msg["To"] = receiver
#     msg["Subject"] = subject

#     msg.attach(MIMEText(body, "plain"))

#     try:
#         server = smtplib.SMTP("smtp.gmail.com", 587)
#         server.starttls()
#         server.login(sender, password)
#         server.send_message(msg)
#         server.quit()

#         print("Email sent")

#     except Exception as e:
#         print("Email failed:", e)



########################################################   FOR ATTACHMENT   ############################################################

# from configparser import ConfigParser
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.mime.base import MIMEBase
# from email import encoders
# import os

# def send_email(subject, body, attachment_path=None): 

#     config = ConfigParser()
#     config.read("Config.ini")

#     sender = config.get("Email", "SENDER")
#     password = config.get("Email", "PASSWORD")
#     receiver = config.get("Email", "RECEIVER")

#     msg = MIMEMultipart()
#     msg["From"] = sender
#     msg["To"] = receiver
#     msg["Subject"] = subject

#     msg.attach(MIMEText(body, "plain"))

#     if attachment_path and os.path.exists(attachment_path):
#         with open(attachment_path, "rb") as f:
#             part = MIMEBase("application", "octet-stream")
#             part.set_payload(f.read())

#         encoders.encode_base64(part)
#         part.add_header(
#             "Content-Disposition",
#             f"attachment; filename={os.path.basename(attachment_path)}"
#         )

#         msg.attach(part)

#     try:
#         server = smtplib.SMTP("smtp.gmail.com", 587)
#         server.starttls()
#         server.login(sender, password)
#         server.send_message(msg)
#         server.quit()

#         print("Email sent")

#     except Exception as e:
#         print("Email failed:", e)



########################################################   FOR ATTACHMENT WITH RETRY LOGIC   ############################################################



from configparser import ConfigParser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import time

def send_email(subject, body, attachment_path=None): 

    config = ConfigParser()
    config.read("c:/Users/vijay_m/OneDrive - Exdion Solutions Pvt. Ltd.-70692290/Documents/Project_Job_Creation/Carroll/config.ini")

    sender = config.get("Email", "SENDER")
    password = config.get("Email", "PASSWORD")
    receiver = config.get("Email", "RECEIVER")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_path)}"
        )

        msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)

        MAX_RETRIES = 3

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                server.send_message(msg)
                print(f"Email sent successfully on attempt {attempt}")
                break

            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")

                if attempt == MAX_RETRIES:
                    print("All retry attempts failed")
                    raise

                time.sleep(5)

        server.quit()

    except Exception as e:
        print("Email failed:", e)