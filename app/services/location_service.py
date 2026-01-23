# app/services/location_service.py
"""
Location service (formerly localidades_service.py).
CRUD and sync operations for states and municipalities using async SQLAlchemy.
"""

from typing import Optional, List

import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.location import State, Municipality
from app.utils.logger import logger


IBGE_STATES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
IBGE_MUNICIPALITIES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


class LocationService:
    """Service for location (state/municipality) operations."""

    @staticmethod
    async def get_states(db: AsyncSession) -> List[State]:
        """Get all states ordered by abbreviation."""
        result = await db.execute(
            select(State).order_by(State.abbreviation)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_state_by_code(db: AsyncSession, ibge_code: int) -> Optional[State]:
        """Get state by IBGE code."""
        result = await db.execute(
            select(State).where(State.ibge_code == ibge_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_state_by_abbreviation(
        db: AsyncSession, 
        abbreviation: str,
    ) -> Optional[State]:
        """Get state by abbreviation (e.g., 'SP')."""
        result = await db.execute(
            select(State)
            .options(selectinload(State.municipalities))
            .where(State.abbreviation == abbreviation.upper())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_municipalities_by_state(
        db: AsyncSession,
        abbreviation: str,
    ) -> Optional[List[Municipality]]:
        """Get all municipalities for a state."""
        state = await LocationService.get_state_by_abbreviation(db, abbreviation)
        if not state:
            return None
        
        result = await db.execute(
            select(Municipality)
            .where(Municipality.state_id == state.id)
            .order_by(Municipality.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_municipality_by_code(
        db: AsyncSession,
        ibge_code: int,
    ) -> Optional[Municipality]:
        """Get municipality by IBGE code."""
        result = await db.execute(
            select(Municipality).where(Municipality.ibge_code == ibge_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def sync_with_ibge(db: AsyncSession) -> dict:
        """
        Synchronize states and municipalities with IBGE API.
        Returns sync statistics.
        """
        stats = {
            "states_created": 0,
            "states_updated": 0,
            "municipalities_created": 0,
            "municipalities_updated": 0,
            "municipalities_skipped": 0,
        }

        async with httpx.AsyncClient() as client:
            # Sync states
            logger.info("Syncing states from IBGE...")
            resp = await client.get(IBGE_STATES_URL)
            resp.raise_for_status()
            states_data = resp.json()

            for state_data in states_data:
                result = await db.execute(
                    select(State).where(State.ibge_code == state_data["id"])
                )
                state = result.scalar_one_or_none()

                if not state:
                    state = State(
                        ibge_code=state_data["id"],
                        abbreviation=state_data.get("sigla"),
                        name=state_data.get("nome"),
                    )
                    db.add(state)
                    stats["states_created"] += 1
                else:
                    state.abbreviation = state_data.get("sigla")
                    state.name = state_data.get("nome")
                    stats["states_updated"] += 1

            await db.commit()
            logger.info(f"States synced: {stats['states_created']} created, {stats['states_updated']} updated")

            # Sync municipalities
            logger.info("Syncing municipalities from IBGE...")
            resp = await client.get(IBGE_MUNICIPALITIES_URL)
            resp.raise_for_status()
            municipalities_data = resp.json()

            for muni_data in municipalities_data:
                muni_code = muni_data.get("id")
                muni_name = muni_data.get("nome")

                # Handle nested structure
                microrregiao = muni_data.get("microrregiao") or {}
                mesorregiao = microrregiao.get("mesorregiao") or {}
                uf = mesorregiao.get("UF") or {}
                uf_code = uf.get("id")

                if not uf_code:
                    logger.warning(f"Municipality without state: {muni_name} ({muni_code})")
                    stats["municipalities_skipped"] += 1
                    continue

                state_result = await db.execute(
                    select(State).where(State.ibge_code == uf_code)
                )
                state = state_result.scalar_one_or_none()

                if not state:
                    logger.warning(f"State {uf_code} not found for municipality {muni_name}")
                    stats["municipalities_skipped"] += 1
                    continue

                muni_result = await db.execute(
                    select(Municipality).where(Municipality.ibge_code == muni_code)
                )
                municipality = muni_result.scalar_one_or_none()

                if not municipality:
                    municipality = Municipality(
                        ibge_code=muni_code,
                        name=muni_name,
                        state_id=state.id,
                    )
                    db.add(municipality)
                    stats["municipalities_created"] += 1
                else:
                    municipality.name = muni_name
                    municipality.state_id = state.id
                    stats["municipalities_updated"] += 1

            await db.commit()
            logger.info(
                f"Municipalities synced: {stats['municipalities_created']} created, "
                f"{stats['municipalities_updated']} updated, "
                f"{stats['municipalities_skipped']} skipped"
            )

        return stats
