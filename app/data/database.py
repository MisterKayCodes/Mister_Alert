from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import settings

DATABASE_URL = settings.database_url

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def init_models():
    """Create all tables defined in models.py if they don't exist."""
    from .models import Base
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
