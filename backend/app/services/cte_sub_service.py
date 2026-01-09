# app/services/cte_sub_service.py

from sqlalchemy.orm import Session
from uuid import UUID

from app.models.cte_subcontratacao import CTeSubcontratacao
from app.schemas.cte_subcontratacao import CTeSubCreate


class CTeSubcontratacaoService:

    @staticmethod
    def adicionar_subcte(
        db: Session,
        carga_id: UUID,
        data: CTeSubCreate
    ) -> CTeSubcontratacao:

        sub = CTeSubcontratacao(
            carga_id=carga_id,
            chave=data.chave,
            cte_cliente_id=data.cte_cliente_id
        )

        sub.xml = data.xml  # criptografia automática

        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    async def adicionar_subcte_enviando_vblog(
        db: Session,
        carga_id: UUID,
        xml: str,
        chave: str,
        vblog,
    ) -> CTeSubcontratacao:
        """Envia para VBLOG e persiste apenas se o envio foi bem sucedido."""
        from app.services.vblog_envdocs_service import VBlogEnvDocsService

        env_service = VBlogEnvDocsService(vblog)
        result = await env_service.enviar_ctes_and_parse([xml])

        if not result:
            raise RuntimeError("Falha ao comunicar com VBLOG ao enviar o documento.")

        parsed = result.get("parsed")
        raw = result.get("raw")

        control_cod = parsed.get("control", {}).get("Cod") if parsed else None
        control_desc = parsed.get("control", {}).get("xDesc") if parsed else None

        found_doc = None
        if parsed:
            for doc in parsed.get("docs", []):
                if doc.get("chDoc") == chave:
                    found_doc = doc
                    break

        success_codes = {"001", "1"}
        doc_success = found_doc is not None and found_doc.get("Cod") in success_codes
        control_success = control_cod in success_codes

        if not (doc_success or control_success):
            reason = found_doc.get("Desc") if found_doc else control_desc or "VBLOG retornou erro"
            raise RuntimeError(f"VBLOG retornou erro ao processar o documento: {reason}")

        sub = CTeSubcontratacao(
            carga_id=carga_id,
            chave=chave,
        )

        sub.xml = xml
        sub.vblog_status_code = found_doc.get("Cod") if found_doc else control_cod
        sub.vblog_status_desc = found_doc.get("Desc") if found_doc else control_desc
        sub.vblog_raw_response = raw
        sub.vblog_attempts = 1

        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub
    @staticmethod
    def listar_por_carga(db: Session, carga_id: UUID):
        return db.query(CTeSubcontratacao).filter(
            CTeSubcontratacao.carga_id == carga_id
        ).all()