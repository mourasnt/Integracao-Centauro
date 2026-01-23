# app/services/vblog/tracking.py
"""
VBLOG/Brudam tracking service for sending tracking events.
Refactored from vblog_tracking.py with shared base class.
"""

import datetime
from typing import Optional, Tuple, List

from app.utils.logger import logger
from app.services.constants import VALID_CODES, VALID_CODES_SET
from .base import VBlogBaseClient


class VBlogTrackingService(VBlogBaseClient):
    """
    Service for sending tracking events to Brudam API.
    """

    def __init__(
        self,
        usuario: Optional[str] = None,
        senha: Optional[str] = None,
        endpoint: Optional[str] = None,
        cliente: Optional[str] = None,
        timeout: float = 10.0,
    ):
        # Tracking uses different auth, so we don't call super().__init__ with cnpj/token
        super().__init__(timeout=timeout)
        self.usuario = usuario
        self.senha = senha
        self.endpoint = endpoint
        self.cliente = cliente

    def build_payload(
        self,
        document_key: str,
        event_code: str,
        event_date: Optional[datetime.datetime] = None,
        observation: Optional[str] = None,
        document_type: str = "NFE",
        attachments: Optional[List[dict]] = None,
    ) -> dict:
        """
        Build JSON payload for tracking event.
        
        Args:
            document_key: Document key (NF-e key)
            event_code: Brudam event code
            event_date: Event timestamp
            observation: Optional observation text
            document_type: Document type (NFE, PEDIDO, etc.)
            attachments: Optional list of attachment dicts
            
        Returns:
            JSON-serializable payload dict
        """
        if event_code not in VALID_CODES_SET:
            raise ValueError(f"Invalid Brudam event code: {event_code}")

        date_fmt = (event_date or datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        document = {
            "cliente": self.cliente,
            "tipo": document_type or "PEDIDO",
            "chave": document_key,
            "eventos": [
                {
                    "codigo": int(event_code),
                    "data": date_fmt,
                    "obs": observation or VALID_CODES[event_code]["message"]
                }
            ]
        }

        if attachments:
            document["anexos"] = attachments

        return {
            "auth": {
                "usuario": self.usuario,
                "senha": self.senha
            },
            "documentos": [document]
        }

    async def send(
        self,
        document_key: str,
        event_code: str,
        event_date: Optional[datetime.datetime] = None,
        observation: Optional[str] = None,
        document_type: str = "NFE",
        attachments: Optional[List[dict]] = None,
    ) -> Tuple[bool, str]:
        """
        Send tracking event to Brudam API.
        
        Args:
            document_key: Document key (NF-e key)
            event_code: Brudam event code
            event_date: Event timestamp
            observation: Optional observation text
            document_type: Document type (NFE, PEDIDO, etc.)
            attachments: Optional list of attachment dicts
            
        Returns:
            Tuple of (success, response_text)
        """
        if not self.endpoint:
            raise ValueError("Brudam tracking endpoint not configured")

        payload = self.build_payload(
            document_key=document_key,
            event_code=event_code,
            event_date=event_date,
            observation=observation,
            document_type=document_type,
            attachments=attachments,
        )

        logger.debug(f"Sending tracking: {document_key} - code {event_code}")

        success, response, status = await self._send_with_retry(
            url=self.endpoint,
            payload=payload,
            content_type="application/json",
        )

        if success:
            logger.info(f"Tracking sent successfully: {document_key}")
        else:
            logger.warning(f"Tracking failed: {document_key} - {response[:200]}")

        return success, response

    # Legacy method alias for backward compatibility
    async def enviar(
        self,
        chave_documento: str,
        codigo_evento: str,
        data_evento: Optional[datetime.datetime] = None,
        obs: Optional[str] = None,
        tipo: str = "NFE",
        anexos: Optional[list] = None,
    ) -> Tuple[bool, str]:
        """Legacy alias for send method."""
        return await self.send(
            document_key=chave_documento,
            event_code=codigo_evento,
            event_date=data_evento,
            observation=obs,
            document_type=tipo,
            attachments=anexos,
        )
