"""
BaseRepository — generic CRUD operations for all repositories.

All repositories MUST extend this class.
Provides type-safe, reusable get/list/create/update/delete operations.

Usage:
    class OfficerRepository(BaseRepository[Officer]):
        def __init__(self, db: AsyncSession):
            super().__init__(Officer, db)
"""

import uuid
from typing import Generic, TypeVar, Any

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository with common CRUD operations."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self._model = model
        self._db = db

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        """Get a single record by UUID primary key."""
        return await self._db.get(self._model, id)

    async def get_one(self, **filters: Any) -> ModelType | None:
        """Get a single record matching the given filters."""
        stmt = select(self._model).filter_by(**filters)
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def get_many(
        self,
        *,
        filters: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 50,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> list[ModelType]:
        """Get a paginated list of records with optional filters."""
        stmt = select(self._model)

        if filters:
            stmt = stmt.filter_by(**filters)

        if order_by and hasattr(self._model, order_by):
            col = getattr(self._model, order_by)
            stmt = stmt.order_by(col.desc() if order_desc else col.asc())

        stmt = stmt.offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """Count records matching the given filters."""
        stmt = select(func.count()).select_from(self._model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    async def create(self, entity: ModelType) -> ModelType:
        """Insert a new record and refresh it."""
        self._db.add(entity)
        await self._db.flush()
        await self._db.refresh(entity)
        return entity

    async def update_by_id(self, id: uuid.UUID, **values: Any) -> None:
        """Update a record by UUID primary key."""
        stmt = (
            update(self._model)
            .where(self._model.id == id)
            .values(**values)
        )
        await self._db.execute(stmt)

    async def delete_by_id(self, id: uuid.UUID) -> None:
        """Delete a record by UUID primary key."""
        stmt = delete(self._model).where(self._model.id == id)
        await self._db.execute(stmt)
