from typing import Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

logger = logging.getLogger(__name__)


class EmailSender:
    """Сервис для отправки email писем"""
    
    def __init__(self):
        """
        Инициализация сервиса отправки email.
        Настройки берутся из core.config.settings
        """
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS
        
        if not self.smtp_host or not self.smtp_user:
            logger.warning(
                "SMTP настройки не заданы. Email отправка будет логироваться, но не отправляться. "
                "Установите SMTP_HOST, SMTP_USER, SMTP_PASSWORD в .env файле"
            )
    
    async def send_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        body: str
    ) -> bool:
        """
        Отправляет email адресанту
        
        Args:
            to_email: Email адрес получателя
            to_name: Имя получателя (опционально)
            subject: Тема письма
            body: Тело письма
            
        Returns:
            True если письмо отправлено успешно
            
        Raises:
            Exception: Если произошла ошибка при отправке
        """
        recipient = f"{to_name} <{to_email}>" if to_name else to_email
        
        if not self.smtp_host or not self.smtp_user:
            logger.info(f"[ЗАГЛУШКА] Отправка email:")
            logger.info(f"  Получатель: {recipient}")
            logger.info(f"  Тема: {subject}")
            logger.info(f"  Тело: {body[:200]}...")
            logger.warning("SMTP не настроен. Письмо не отправлено. Настройте SMTP в .env файле.")
            return True
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Email успешно отправлен: {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке email: {e}")
            raise Exception(f"Не удалось отправить email: {str(e)}")

