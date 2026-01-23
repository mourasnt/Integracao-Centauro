# tests/test_locations.py
"""
Tests for location (state/municipality) services.
Tests the service layer directly to avoid session isolation issues.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models.base import Base
from app.models.location import State, Municipality
from app.services.location_service import LocationService


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_location_service_get_states(test_db):
    """Test LocationService.get_states."""
    sp = State(name="São Paulo", abbreviation="SP", ibge_code=35)
    rj = State(name="Rio de Janeiro", abbreviation="RJ", ibge_code=33)
    
    test_db.add_all([sp, rj])
    await test_db.commit()
    
    states = await LocationService.get_states(test_db)
    
    assert len(states) == 2
    abbreviations = {s.abbreviation for s in states}
    assert "SP" in abbreviations
    assert "RJ" in abbreviations


@pytest.mark.asyncio
async def test_location_service_get_municipalities_by_state(test_db):
    """Test LocationService.get_municipalities_by_state."""
    sp = State(name="São Paulo", abbreviation="SP", ibge_code=35)
    test_db.add(sp)
    await test_db.commit()
    await test_db.refresh(sp)
    
    campinas = Municipality(name="Campinas", ibge_code=3509502, state_id=sp.id)
    sorocaba = Municipality(name="Sorocaba", ibge_code=3552205, state_id=sp.id)
    test_db.add_all([campinas, sorocaba])
    await test_db.commit()
    
    municipalities = await LocationService.get_municipalities_by_state(test_db, "SP")
    
    assert municipalities is not None
    assert len(municipalities) == 2
    names = {m.name for m in municipalities}
    assert "Campinas" in names
    assert "Sorocaba" in names


@pytest.mark.asyncio
async def test_location_service_get_municipality_by_code(test_db):
    """Test LocationService.get_municipality_by_code."""
    sp = State(name="São Paulo", abbreviation="SP", ibge_code=35)
    test_db.add(sp)
    await test_db.commit()
    await test_db.refresh(sp)
    
    campinas = Municipality(name="Campinas", ibge_code=3509502, state_id=sp.id)
    test_db.add(campinas)
    await test_db.commit()
    
    result = await LocationService.get_municipality_by_code(test_db, 3509502)
    
    assert result is not None
    assert result.name == "Campinas"
    assert result.ibge_code == 3509502


@pytest.mark.asyncio
async def test_location_service_nonexistent_state(test_db):
    """Test getting municipalities for nonexistent state."""
    result = await LocationService.get_municipalities_by_state(test_db, "XX")
    assert result is None


@pytest.mark.asyncio
async def test_location_service_nonexistent_municipality(test_db):
    """Test getting nonexistent municipality."""
    result = await LocationService.get_municipality_by_code(test_db, 9999999)
    assert result is None
