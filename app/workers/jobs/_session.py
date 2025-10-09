from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

_engine = create_async_engine(settings.database_url, future=True)
_Session = async_sessionmaker(_engine, expire_on_commit=False, autoflush=False)

class session_scope:
    """Context manager asíncrono para crear/cerrar sesión en tareas Celery."""
    def __init__(self) -> None:
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = _Session()
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()
