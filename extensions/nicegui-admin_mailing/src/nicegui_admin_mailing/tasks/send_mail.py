import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from celery.utils.log import get_task_logger
from html2text import html2text

# from nicegui_admin_new import celery
from nicegui_admin_new.task import NiceguiAdminBaseTask

from nicegui_admin_mailing.extension import MailingExtension, mailing_extension

logger = get_task_logger(__name__)

mailing_extension_settings: MailingExtension.Settings = mailing_extension.settings


# @celery.task(bind=True)
def send_mail(self: NiceguiAdminBaseTask,
              recipient: str,
              subject: str,
              html_str: str) -> bool:
    logger.info(f"Send mail task started ...")
    self.update_state(state="PROGRESS", meta={"progress": 0})

    server = None
    try:
        # build body and attachments
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = formataddr((mailing_extension_settings.sender_display_name,
                                      mailing_extension_settings.sender_email))
        message["To"] = recipient

        # create a text/plain version of the html message
        plaintext_str = html2text(html_str)

        # Turn these into plain/html MIMEText objects
        plaintext = MIMEText(plaintext_str, "plain")
        html = MIMEText(html_str, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(plaintext)
        message.attach(html)
        self.update_state(state="PROGRESS", meta={"progress": 20})

        # connect to smtp server
        logger.info(f"Connecting to SMTP server ...\n"
                    f"Server: {mailing_extension_settings.smtp_server}\n"
                    f"Port: {mailing_extension_settings.smtp_port}\n"
                    f"Use SSL: {mailing_extension_settings.smtp_use_ssl}\n"
                    f"Timeout: {mailing_extension_settings.smtp_timeout}\n"
                    f"Username: {mailing_extension_settings.smtp_username}\n"
                    f"Password: ***")
        if mailing_extension_settings.smtp_use_ssl == MailingExtension.Settings.Encryption.NO_ENCRYPTION:
            # Connect to the SMTP server using SSL
            server = smtplib.SMTP(host=mailing_extension_settings.smtp_server,
                                  port=mailing_extension_settings.smtp_port,
                                  timeout=mailing_extension_settings.smtp_timeout)
            logger.info("Connecting to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 33})

            logger.info("Logging in to SMTP server ...")
            server.login(mailing_extension_settings.smtp_username,
                         mailing_extension_settings.smtp_password)
            logger.info("Logging in to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 45})
        elif mailing_extension_settings.smtp_use_ssl == MailingExtension.Settings.Encryption.SSL:
            # Create a secure SSL context
            context = ssl.create_default_context()

            # Connect to the SMTP server without SSL (no TLS)
            server = smtplib.SMTP_SSL(host=mailing_extension_settings.smtp_server,
                                      port=mailing_extension_settings.smtp_port,
                                      timeout=mailing_extension_settings.smtp_timeout,
                                      context=context)
            logger.info("Connecting to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 33})

            logger.info("Logging in to SMTP server ...")
            server.login(mailing_extension_settings.smtp_username,
                         mailing_extension_settings.smtp_password)
            logger.info("Logging in to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 50})
        elif mailing_extension_settings.smtp_use_ssl == MailingExtension.Settings.Encryption.STARTTLS:
            # Create a secure SSL context
            context = ssl.create_default_context()

            # Connect to the SMTP server without SSL
            server = smtplib.SMTP(host=mailing_extension_settings.smtp_server,
                                  port=mailing_extension_settings.smtp_port,
                                  timeout=mailing_extension_settings.smtp_timeout)
            logger.info("Connecting to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 41})

            # send ehlo
            logger.info("Sending EHLO to SMTP server ...")
            server.ehlo()
            logger.info("Sending EHLO to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 42})

            # create secure connection with starttls
            logger.info("Connecting to SMTP server (STARTTLS) ...")
            server.starttls(context=context)
            logger.info("Connecting to SMTP server (STARTTLS) successfully.')")
            self.update_state(state="PROGRESS", meta={"progress": 43})

            # send ehlo again
            logger.info("Sending EHLO to SMTP server (STARTTLS) ...')")
            server.ehlo()
            logger.info("Sending EHLO to SMTP server (STARTTLS) successfully.')')')")
            self.update_state(state="PROGRESS", meta={"progress": 44})

            logger.info("Logging in to SMTP server ...")
            server.login(mailing_extension_settings.smtp_username,
                         mailing_extension_settings.smtp_password)
            logger.info("Logging in to SMTP server successfully.")
            self.update_state(state="PROGRESS", meta={"progress": 45})
        else:
            raise ValueError(f"Invalid encryption type: {mailing_extension_settings.smtp_use_ssl}")

        # send email
        logger.info(f"Sending mail to '{recipient}' ...")
        server.sendmail(from_addr=mailing_extension_settings.sender_email,
                        to_addrs=recipient,
                        msg=message.as_string(),
                        mail_options=[],
                        rcpt_options=[])
        logger.info(f"Sending mail to '{recipient}' successfully.")
        self.update_state(state="PROGRESS", meta={"progress": 66})
    except Exception as e:
        logger.error(f"Error connecting to SMTP server:\n{e}")
        return False
    finally:
        if server is not None:
            server.quit()

    logger.info(f"Send mail task completed.")
    self.update_state(state="PROGRESS", meta={"progress": 100})

    return True
