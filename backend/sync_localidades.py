import sys
import os
import time
import httpx #type: ignore
from sqlalchemy.orm import Session

# -------------------------------------------------------
# Ajusta PATH para permitir 'import app'
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# -------------------------------------------------------
# Importações da aplicação (carrega TODOS os models)
# -------------------------------------------------------
from app.core.database import SessionLocal, engine
import app.models  # IMPORTANTE: garante que SQLAlchemy carregue todos os models

from app.models.localidade import Estado, Municipio


# -------------------------------------------------------
# URLs IBGE
# -------------------------------------------------------
IBGE_ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
IBGE_MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


# -------------------------------------------------------
# Helper para requisições com retry
# -------------------------------------------------------
def fetch_json(url: str, retries: int = 3, wait: float = 1.5):
    for i in range(retries):
        try:
            resp = httpx.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ERRO] Falha ao consultar {url}: {e}")
            if i < retries - 1:
                print(f"Tentando novamente ({i+1}/{retries})...")
                time.sleep(wait)
    raise RuntimeError(f"Erro permanente ao acessar {url}")


# -------------------------------------------------------
# Sincronização principal
# -------------------------------------------------------
def sincronizar_localidades():
    db: Session = SessionLocal()

    def safe(d):
        return d if isinstance(d, dict) else {}

    try:
        # 1) Estados
        resp_estados = httpx.get(IBGE_ESTADOS_URL)
        resp_estados.raise_for_status()
        estados = resp_estados.json()

        mapa_estados = {}

        for e in estados:
            uf_id = e["id"]
            sigla = e["sigla"]
            nome = e["nome"]

            estado_obj = db.query(Estado).filter_by(codigo_ibge=uf_id).first()

            if not estado_obj:
                estado_obj = Estado(
                    codigo_ibge=uf_id,
                    sigla=sigla,
                    nome=nome
                )
                db.add(estado_obj)
            else:
                estado_obj.sigla = sigla
                estado_obj.nome = nome

            mapa_estados[uf_id] = estado_obj

        db.commit()

        # 2) Municípios
        resp_munis = httpx.get(IBGE_MUNICIPIOS_URL)
        resp_munis.raise_for_status()
        municipios = resp_munis.json()

        for m in municipios:

            muni_id = m["id"]
            muni_nome = m["nome"]

            microrregiao = safe(m.get("microrregiao"))
            mesorregiao = safe(microrregiao.get("mesorregiao"))
            uf_info = safe(mesorregiao.get("UF"))

            uf_id = uf_info.get("id")

            if not uf_id:
                print(f"[!] Município sem UF detectado: {muni_nome} — ignorando")
                continue

            estado_obj = mapa_estados.get(uf_id)

            if not estado_obj:
                print(f"[!] UF {uf_id} não encontrada para município {muni_nome}")
                continue

            muni_obj = db.query(Municipio).filter_by(codigo_ibge=muni_id).first()

            if not muni_obj:
                muni_obj = Municipio(
                    codigo_ibge=muni_id,
                    nome=muni_nome,
                    estado_id=estado_obj.id,
                )
                db.add(muni_obj)
                print(f"[+] Município cadastrado: {muni_nome} ({estado_obj.sigla})")
            else:
                muni_obj.nome = muni_nome
                muni_obj.estado_id = estado_obj.id

        db.commit()

    finally:
        db.close()


    print("\n============================================")
    print("  FINALIZADO COM SUCESSO!")
    print("============================================\n")


# -------------------------------------------------------
# Execução direta
# -------------------------------------------------------
if __name__ == "__main__":
    sincronizar_localidades()
