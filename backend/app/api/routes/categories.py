from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.category import ServiceCategory
from app.schemas.category import CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    stmt = select(ServiceCategory).order_by(ServiceCategory.name.asc())
    result = await db.execute(stmt)
    categories = result.scalars().all()
    return [CategoryResponse.model_validate(c) for c in categories]
