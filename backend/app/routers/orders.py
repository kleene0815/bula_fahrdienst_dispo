import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import DisponentUser
from app.database import get_db
from app.events import broadcaster
from app.models import Order, StatusLog, TripOrder
from app.schemas.orders import OrderCreate, OrderOut, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])

VALID_STATUSES = {"offen", "zugeteilt", "unterwegs", "erledigt", "storniert"}


@router.get("", response_model=list[OrderOut])
async def list_orders(
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
):
    query = select(Order).order_by(Order.deadline)
    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Ungültiger Status: {status}")
        query = query.where(Order.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    current_user: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    order = Order(**body.model_dump(), created_by=current_user.id)
    db.add(order)
    db.add(StatusLog(
        entity_type="order",
        entity_id=order.id,
        old_status=None,
        new_status="offen",
        changed_by=current_user.id,
    ))
    await db.commit()
    await db.refresh(order)
    await broadcaster.broadcast("order_created", OrderOut.model_validate(order).model_dump())
    return order


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: uuid.UUID,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
    return order


@router.patch("/{order_id}", response_model=OrderOut)
async def update_order(
    order_id: uuid.UUID,
    body: OrderUpdate,
    current_user: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
    if order.status not in ("offen", "zugeteilt"):
        raise HTTPException(status_code=409, detail="Auftrag kann in diesem Status nicht bearbeitet werden")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(order, field, value)

    await db.commit()
    await db.refresh(order)
    await broadcaster.broadcast("order_updated", OrderOut.model_validate(order).model_dump())
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: uuid.UUID,
    current_user: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
    if order.status == "storniert":
        raise HTTPException(status_code=409, detail="Auftrag ist bereits storniert")

    # Aus Fahrt entfernen falls zugewiesen
    trip_order = await db.execute(
        select(TripOrder).where(TripOrder.order_id == order_id)
    )
    to = trip_order.scalar_one_or_none()
    if to:
        await db.delete(to)

    old_status = order.status
    order.status = "storniert"
    db.add(StatusLog(
        entity_type="order",
        entity_id=order.id,
        old_status=old_status,
        new_status="storniert",
        changed_by=current_user.id,
    ))
    await db.commit()
    await db.refresh(order)
    await broadcaster.broadcast("order_updated", OrderOut.model_validate(order).model_dump())
    return order
