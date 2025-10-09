from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.listing_photo import ListingPhoto
from .base import BaseRepository

class ListingPhotoRepository(BaseRepository[ListingPhoto]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ListingPhoto)

    async def add_photo(
        self,
        *,
        listing_id: str,
        storage_key: str,
        image_url: str | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> ListingPhoto:
        photo = ListingPhoto(
            listing_id=listing_id,
            storage_key=storage_key,
            image_url=image_url,
            width=width,
            height=height,
        )
        return await self.add(photo)
