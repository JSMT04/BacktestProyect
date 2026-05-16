"""Strategies router — CRUD endpoints for trading strategies."""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.orm_models import Strategy as StrategyORM, StrategyVersion as StrategyVersionORM
from models.schemas import StrategyCreateRequest, StrategyResponse, StrategyListItem

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StrategyResponse)
async def create_strategy(request: StrategyCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new strategy."""
    # Create main strategy record
    strategy = StrategyORM(
        name=request.name,
        description=request.description,
        current_version=1
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)

    # Create initial version record
    version = StrategyVersionORM(
        strategy_id=strategy.id,
        version=1,
        strategy_data=json.dumps(request.strategy_data)
    )
    db.add(version)
    await db.commit()

    return StrategyResponse(
        strategy_id=strategy.id,
        name=strategy.name,
        version=1,
        created_at=strategy.created_at
    )


@router.get("", response_model=List[StrategyListItem])
async def list_strategies(db: AsyncSession = Depends(get_db)):
    """List all strategies."""
    result = await db.execute(select(StrategyORM).order_by(StrategyORM.updated_at.desc()))
    strategies = result.scalars().all()
    
    return [
        StrategyListItem(
            strategy_id=s.id,
            name=s.name,
            description=s.description,
            current_version=s.current_version,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in strategies
    ]


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str, db: AsyncSession = Depends(get_db)):
    """Get a strategy with all its versions."""
    result = await db.execute(select(StrategyORM).where(StrategyORM.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    versions_result = await db.execute(
        select(StrategyVersionORM)
        .where(StrategyVersionORM.strategy_id == strategy_id)
        .order_by(StrategyVersionORM.version.desc())
    )
    versions = versions_result.scalars().all()
    
    return {
        "strategy_id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "current_version": strategy.current_version,
        "created_at": strategy.created_at,
        "updated_at": strategy.updated_at,
        "versions": [
            {
                "version": v.version,
                "strategy_data": json.loads(v.strategy_data),
                "created_at": v.created_at
            } for v in versions
        ]
    }


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(strategy_id: str, request: StrategyCreateRequest, db: AsyncSession = Depends(get_db)):
    """Update a strategy (creates a new version)."""
    result = await db.execute(select(StrategyORM).where(StrategyORM.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    # Increment version
    new_version_num = strategy.current_version + 1
    strategy.name = request.name
    strategy.description = request.description
    strategy.current_version = new_version_num
    
    # Create new version record
    new_version = StrategyVersionORM(
        strategy_id=strategy.id,
        version=new_version_num,
        strategy_data=json.dumps(request.strategy_data)
    )
    db.add(new_version)
    await db.commit()
    await db.refresh(strategy)
    
    return StrategyResponse(
        strategy_id=strategy.id,
        name=strategy.name,
        version=new_version_num,
        created_at=strategy.updated_at
    )


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a strategy and all its versions."""
    result = await db.execute(select(StrategyORM).where(StrategyORM.id == strategy_id))
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    await db.delete(strategy)
    await db.commit()
    
    return {"strategy_id": strategy_id, "status": "deleted"}
