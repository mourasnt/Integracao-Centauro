import httpx #type: ignore
from sqlalchemy.orm import Session
from app.models.localidade import Estado, Municipio


IBGE_ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
IBGE_MUNIS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


class LocalidadesService:

    @staticmethod
    def get_estados(db: Session):
        return db.query(Estado).order_by(Estado.sigla).all()

    @staticmethod
    def get_municipios_por_uf(db: Session, uf: str):
        uf = uf.upper()
        estado = db.query(Estado).filter(Estado.sigla == uf).first()
        if not estado:
            return None
        return (
            db.query(Municipio)
            .filter(Municipio.estado_id == estado.id)
            .order_by(Municipio.nome)
            .all()
        )

    @staticmethod
    def get_municipio_por_codigo(db: Session, codigo_ibge: int):
        return db.query(Municipio).filter(Municipio.codigo_ibge == codigo_ibge).first()
    
    @staticmethod
    def get_estado_por_codigo(db: Session, codigo_ibge: int):
        return db.query(Estado).filter(Estado.codigo_ibge == codigo_ibge).first()

    @staticmethod
    def sincronizar_com_ibge(db: Session):

        # -----------------------------------
        # 1 — ESTADOS
        # -----------------------------------
        resp = httpx.get(IBGE_ESTADOS_URL)
        resp.raise_for_status()
        estados = resp.json()

        for e in estados:
            estado = (
                db.query(Estado)
                .filter(Estado.codigo_ibge == e["id"])
                .first()
            )

            if not estado:
                estado = Estado(
                    codigo_ibge=e["id"],
                    sigla=e.get("sigla"),
                    nome=e.get("nome"),
                )
                db.add(estado)
            else:
                estado.sigla = e.get("sigla")
                estado.nome = e.get("nome")

        db.commit()

        # -----------------------------------
        # 2 — MUNICÍPIOS (tratamento resiliente)
        # -----------------------------------
        resp = httpx.get(IBGE_MUNIS_URL)
        resp.raise_for_status()
        municipios = resp.json()

        for m in municipios:

            muni_codigo = m.get("id")
            muni_nome = m.get("nome")

            # 🔥 Alguns municípios vêm sem microrregiao → tratar caso a caso
            microrregiao = m.get("microrregiao") or {}
            mesorregiao = microrregiao.get("mesorregiao") or {}
            uf = mesorregiao.get("UF") or {}

            uf_id = uf.get("id")  # pode ser None → se for, ignoramos

            if not uf_id:
                # ⚠️ Município sem UF — registrar warning ou ignorar
                print(f"[WARN] Município sem UF: {muni_nome} ({muni_codigo})")
                continue

            estado = (
                db.query(Estado)
                .filter(Estado.codigo_ibge == uf_id)
                .first()
            )

            if not estado:
                print(f"[WARN] UF {uf_id} não encontrada para município {muni_nome}")
                continue

            muni = (
                db.query(Municipio)
                .filter(Municipio.codigo_ibge == muni_codigo)
                .first()
            )

            if not muni:
                muni = Municipio(
                    codigo_ibge=muni_codigo,
                    nome=muni_nome,
                    estado_id=estado.id,
                )
                db.add(muni)
            else:
                muni.nome = muni_nome
                muni.estado_id = estado.id

        db.commit()