import logging
import secrets
import uuid
from datetime import datetime
from types import SimpleNamespace
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser, DisponentUser, FahrerUser
from app.database import get_db, AsyncSessionLocal
from app.events import broadcaster
from app.models import AppConfig, Order, StatusLog, Trip, TripOrder, User, Vehicle
from app.schemas.orders import OrderOut
from app.schemas.trips import TripCreate, TripOut, TripUpdate
from app.services.routing import calculate_route_for_trip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["trips"])


async def _run_route_calculation(trip_id: uuid.UUID) -> None:
    """Background-Task: Fahrtdauer und Startzeit berechnen und per SSE broadcasten."""
    async with AsyncSessionLocal() as db:
        try:
            trip = await _load_trip(db, trip_id)
            config = await db.get(AppConfig, 1)
            if not config or not config.routing_api_key:
                return
            await calculate_route_for_trip(trip, config, db)
            await db.commit()
            trip = await _load_trip(db, trip_id)
            await broadcaster.broadcast("trip_updated", TripOut.from_orm_trip(trip).model_dump())
        except Exception as exc:
            logger.warning("Routenberechnung fehlgeschlagen (trip %s): %s", trip_id, exc)
            async with AsyncSessionLocal() as db2:
                trip2 = await db2.get(Trip, trip_id)
                if trip2:
                    trip2.estimated_duration_minutes = None
                    if not trip2.start_time_manual_override:
                        trip2.planned_start_time = None
                    await db2.commit()


def _trip_query():
    return select(Trip).options(
        selectinload(Trip.driver).selectinload(User.roles),
        selectinload(Trip.vehicle),
        selectinload(Trip.trip_orders).selectinload(TripOrder.order),
    )


def _compute_seats(orders: list[Order]) -> int:
    seats = 1  # Fahrersitz
    for o in orders:
        if o.patient_name:
            seats += 1
            if o.companion:
                seats += 1
    return seats


async def _detach_from_other_trip(
    db: AsyncSession,
    order: "Order",
    excluding_trip_id: uuid.UUID | None,
) -> "uuid.UUID | None":
    """Löst einen Auftrag aus einer anderen geplanten Fahrt heraus.
    Gibt die ID der alten Fahrt zurück, oder None wenn keine Verschiebung möglich war."""
    result = await db.execute(select(TripOrder).where(TripOrder.order_id == order.id))
    to = result.scalar_one_or_none()
    if not to or to.trip_id == excluding_trip_id:
        return None
    old_trip = await db.get(Trip, to.trip_id)
    if not old_trip or old_trip.status != "geplant":
        return None
    await db.delete(to)
    return to.trip_id


async def _load_trip(db: AsyncSession, trip_id: uuid.UUID) -> Trip:
    result = await db.execute(
        _trip_query().where(Trip.id == trip_id),
        execution_options={"populate_existing": True},
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Fahrt nicht gefunden")
    return trip


@router.get("", response_model=list[TripOut])
async def list_trips(
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    include_completed: bool = False,
):
    query = _trip_query()
    if not include_completed:
        query = query.where(Trip.status.in_(["geplant", "aktiv"]))
    result = await db.execute(query.order_by(Trip.created_at))
    return [TripOut.from_orm_trip(t) for t in result.scalars().all()]


@router.get("/mine", response_model=list[TripOut])
async def list_my_trips(
    current_user: FahrerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        _trip_query()
        .where(Trip.driver_id == current_user.id)
        .where(Trip.status.in_(["geplant", "aktiv"]))
        .order_by(Trip.created_at)
    )
    return [TripOut.from_orm_trip(t) for t in result.scalars().all()]


@router.get("/by-token/{qr_token}", response_model=TripOut)
async def get_trip_by_token(
    qr_token: str,
    _: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(_trip_query().where(Trip.qr_token == qr_token))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="Fahrt nicht gefunden")
    return TripOut.from_orm_trip(trip)


class PreviewRouteBody(BaseModel):
    order_ids: list[uuid.UUID]


class PreviewRouteOut(BaseModel):
    planned_start_time: datetime | None
    estimated_duration_minutes: int | None


@router.post("/preview_route", response_model=PreviewRouteOut)
async def preview_route(
    body: PreviewRouteBody,
    current_user: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Berechnet Startzeit und Dauer für eine Auftragsfolge ohne gespeicherte Fahrt."""
    if not body.order_ids:
        return PreviewRouteOut(planned_start_time=None, estimated_duration_minutes=None)

    config = await db.get(AppConfig, 1)
    if not config or not config.routing_api_key or config.routing_mode != "auto":
        return PreviewRouteOut(planned_start_time=None, estimated_duration_minutes=None)

    orders_result = await db.execute(select(Order).where(Order.id.in_(body.order_ids)))
    orders_by_id = {o.id: o for o in orders_result.scalars().all()}

    fake_trip_orders = [
        SimpleNamespace(order=orders_by_id[oid], sort_order=i + 1)
        for i, oid in enumerate(body.order_ids)
        if oid in orders_by_id
    ]
    if not fake_trip_orders:
        return PreviewRouteOut(planned_start_time=None, estimated_duration_minutes=None)

    fake_trip = SimpleNamespace(
        trip_orders=fake_trip_orders,
        planned_start_time=None,
        estimated_duration_minutes=None,
        start_time_manual_override=False,
    )

    try:
        await calculate_route_for_trip(fake_trip, config, db)
        await db.flush()  # config.routing_remaining_requests persistieren
    except Exception as exc:
        logger.warning("Preview-Routenberechnung fehlgeschlagen: %s", exc)
        return PreviewRouteOut(planned_start_time=None, estimated_duration_minutes=None)

    return PreviewRouteOut(
        planned_start_time=fake_trip.planned_start_time,
        estimated_duration_minutes=fake_trip.estimated_duration_minutes,
    )


@router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
async def create_trip(
    body: TripCreate,
    current_user: DisponentUser,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not body.order_ids:
        raise HTTPException(status_code=400, detail="Mindestens ein Auftrag erforderlich")

    # Aufträge laden und prüfen
    orders_result = await db.execute(
        select(Order).where(Order.id.in_(body.order_ids))
    )
    orders = list(orders_result.scalars().all())
    if len(orders) != len(body.order_ids):
        raise HTTPException(status_code=400, detail="Ein oder mehrere Aufträge nicht gefunden")

    relocated_from: set[uuid.UUID] = set()
    for o in orders:
        if o.status == "zugeteilt":
            old_trip_id = await _detach_from_other_trip(db, o, None)
            if old_trip_id is None:
                raise HTTPException(status_code=409, detail=f"Auftrag {o.id} kann nicht zugeteilt werden (Status: {o.status})")
            relocated_from.add(old_trip_id)
        elif o.status != "offen":
            raise HTTPException(status_code=409, detail=f"Auftrag {o.id} ist nicht offen (Status: {o.status})")

    # Kapazitätsprüfung (nur wenn Fahrzeug gewählt)
    if body.vehicle_id:
        vehicle = await db.get(Vehicle, body.vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")
        needed = _compute_seats(orders)
        if needed > vehicle.seats:
            raise HTTPException(status_code=409, detail=f"Kapazität überschritten: {needed} von {vehicle.seats} Sitzen belegt")

    # Nächste trip_number ermitteln
    from sqlalchemy import func as sqlfunc
    max_result = await db.execute(select(sqlfunc.max(Trip.trip_number)))
    max_num = max_result.scalar_one_or_none() or 0

    trip = Trip(
        trip_number=max_num + 1,
        name=body.name,
        driver_id=body.driver_id,
        vehicle_id=body.vehicle_id,
        qr_token=secrets.token_hex(32),
        notes=body.notes,
    )
    db.add(trip)
    await db.flush()

    for i, order_id in enumerate(body.order_ids):
        db.add(TripOrder(trip_id=trip.id, order_id=order_id, sort_order=i + 1))

    for o in orders:
        if o.status != "zugeteilt":
            o.status = "zugeteilt"
            db.add(StatusLog(entity_type="order", entity_id=o.id, old_status="offen", new_status="zugeteilt", changed_by=current_user.id))

    db.add(StatusLog(entity_type="trip", entity_id=trip.id, old_status=None, new_status="geplant", changed_by=current_user.id))
    await db.commit()

    trip = await _load_trip(db, trip.id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_created", out.model_dump())
    for to in trip.trip_orders:
        await broadcaster.broadcast("order_updated", OrderOut.model_validate(to.order).model_dump())
    for old_trip_id in relocated_from:
        old_trip_obj = await _load_trip(db, old_trip_id)
        await broadcaster.broadcast("trip_updated", TripOut.from_orm_trip(old_trip_obj).model_dump())

    config = await db.get(AppConfig, 1)
    if config and config.routing_api_key and config.routing_mode == "auto":
        try:
            await calculate_route_for_trip(trip, config, db)
            await db.commit()
            trip = await _load_trip(db, trip.id)
            out = TripOut.from_orm_trip(trip)
            await broadcaster.broadcast("trip_updated", out.model_dump())
        except Exception as exc:
            logger.warning("Routenberechnung fehlgeschlagen (trip %s): %s", trip.id, exc)

    return out


@router.get("/{trip_id}", response_model=TripOut)
async def get_trip(
    trip_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    user_roles = {r.role for r in current_user.roles}
    if "disponent" not in user_roles and trip.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Fehlende Berechtigung")
    return TripOut.from_orm_trip(trip)


@router.patch("/{trip_id}", response_model=TripOut)
async def update_trip(
    trip_id: uuid.UUID,
    body: TripUpdate,
    current_user: DisponentUser,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    if trip.status != "geplant":
        raise HTTPException(status_code=409, detail="Fahrt kann nur im Status 'geplant' bearbeitet werden")

    fields = body.model_fields_set
    if 'name' in fields:
        trip.name = body.name
    if 'driver_id' in fields:
        trip.driver_id = body.driver_id
    if 'vehicle_id' in fields:
        trip.vehicle_id = body.vehicle_id
    if 'notes' in fields:
        trip.notes = body.notes
    if body.clear_start_time_override:
        trip.start_time_manual_override = False
        trip.planned_start_time = None
    elif 'planned_start_time' in fields and body.planned_start_time is not None:
        trip.planned_start_time = body.planned_start_time.replace(tzinfo=None)
        trip.start_time_manual_override = True

    freed_orders: list[Order] = []
    relocated_from: set[uuid.UUID] = set()
    if body.order_ids is not None:
        # Alte Aufträge freigeben
        old_order_ids = {to.order_id for to in trip.trip_orders}
        new_order_ids = set(body.order_ids)

        for to in list(trip.trip_orders):
            if to.order_id not in new_order_ids:
                order = await db.get(Order, to.order_id)
                if order:
                    order.status = "offen"
                    db.add(StatusLog(entity_type="order", entity_id=order.id, old_status="zugeteilt", new_status="offen", changed_by=current_user.id))
                    freed_orders.append(order)
                await db.delete(to)

        # Neue Aufträge hinzufügen
        orders_result = await db.execute(select(Order).where(Order.id.in_(new_order_ids - old_order_ids)))
        new_orders = list(orders_result.scalars().all())
        for o in new_orders:
            if o.status == "zugeteilt":
                old_trip_id = await _detach_from_other_trip(db, o, trip_id)
                if old_trip_id is None:
                    raise HTTPException(status_code=409, detail=f"Auftrag {o.id} kann nicht verschoben werden")
                relocated_from.add(old_trip_id)
            elif o.status != "offen":
                raise HTTPException(status_code=409, detail=f"Auftrag {o.id} ist nicht offen")
            else:
                o.status = "zugeteilt"
                db.add(StatusLog(entity_type="order", entity_id=o.id, old_status="offen", new_status="zugeteilt", changed_by=current_user.id))

        # Reihenfolge neu setzen
        await db.flush()
        for i, oid in enumerate(body.order_ids):
            existing = next((to for to in trip.trip_orders if to.order_id == oid), None)
            if existing:
                existing.sort_order = i + 1
            else:
                db.add(TripOrder(trip_id=trip.id, order_id=oid, sort_order=i + 1))

        # Kapazitätsprüfung
        if trip.vehicle_id:
            vehicle = await db.get(Vehicle, trip.vehicle_id)
            all_orders_result = await db.execute(select(Order).where(Order.id.in_(body.order_ids)))
            all_orders = list(all_orders_result.scalars().all())
            if vehicle and _compute_seats(all_orders) > vehicle.seats:
                raise HTTPException(status_code=409, detail="Kapazität überschritten")

    await db.commit()
    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    for to in trip.trip_orders:
        await broadcaster.broadcast("order_updated", OrderOut.model_validate(to.order).model_dump())
    for order in freed_orders:
        await db.refresh(order)
        await broadcaster.broadcast("order_updated", OrderOut.model_validate(order).model_dump())
    for old_trip_id in relocated_from:
        old_trip_obj = await _load_trip(db, old_trip_id)
        await broadcaster.broadcast("trip_updated", TripOut.from_orm_trip(old_trip_obj).model_dump())

    orders_changed = body.order_ids is not None
    if orders_changed and not trip.start_time_manual_override:
        config = await db.get(AppConfig, 1)
        if config and config.routing_api_key and config.routing_mode == "auto":
            try:
                await calculate_route_for_trip(trip, config, db)
                await db.commit()
                trip = await _load_trip(db, trip_id)
                out = TripOut.from_orm_trip(trip)
                await broadcaster.broadcast("trip_updated", out.model_dump())
            except Exception as exc:
                logger.warning("Routenberechnung fehlgeschlagen (trip %s): %s", trip_id, exc)

    return out


@router.post("/{trip_id}/start", response_model=TripOut)
async def start_trip(
    trip_id: uuid.UUID,
    current_user: FahrerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    user_roles = {r.role for r in current_user.roles}
    if "disponent" not in user_roles and trip.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Fehlende Berechtigung")
    if trip.status != "geplant":
        raise HTTPException(status_code=409, detail="Fahrt ist nicht im Status 'geplant'")

    trip.status = "aktiv"
    trip.started_at = datetime.utcnow()
    db.add(StatusLog(entity_type="trip", entity_id=trip.id, old_status="geplant", new_status="aktiv", changed_by=current_user.id))

    for to in trip.trip_orders:
        to.order.status = "unterwegs"
        db.add(StatusLog(entity_type="order", entity_id=to.order.id, old_status="zugeteilt", new_status="unterwegs", changed_by=current_user.id))

    await db.commit()
    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    for to in trip.trip_orders:
        await broadcaster.broadcast("order_updated", OrderOut.model_validate(to.order).model_dump())
    return out


@router.post("/{trip_id}/orders/{order_id}/complete", response_model=TripOut)
async def complete_stop(
    trip_id: uuid.UUID,
    order_id: uuid.UUID,
    current_user: FahrerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    user_roles = {r.role for r in current_user.roles}
    if "disponent" not in user_roles and trip.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Fehlende Berechtigung")
    if trip.status != "aktiv":
        raise HTTPException(status_code=409, detail="Fahrt ist nicht aktiv")

    to = next((x for x in trip.trip_orders if x.order_id == order_id), None)
    if not to:
        raise HTTPException(status_code=404, detail="Auftrag gehört nicht zu dieser Fahrt")
    if to.order.status != "unterwegs":
        raise HTTPException(status_code=409, detail="Auftrag ist nicht im Status 'unterwegs'")

    to.order.status = "erledigt"
    db.add(StatusLog(entity_type="order", entity_id=order_id, old_status="unterwegs", new_status="erledigt", changed_by=current_user.id))
    await db.commit()

    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    completed_to = next((x for x in trip.trip_orders if x.order_id == order_id), None)
    if completed_to:
        await broadcaster.broadcast("order_updated", OrderOut.model_validate(completed_to.order).model_dump())
    return out


@router.post("/{trip_id}/complete", response_model=TripOut)
async def complete_trip(
    trip_id: uuid.UUID,
    current_user: FahrerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    user_roles = {r.role for r in current_user.roles}
    if "disponent" not in user_roles and trip.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Fehlende Berechtigung")
    if trip.status != "aktiv":
        raise HTTPException(status_code=409, detail="Fahrt ist nicht aktiv")

    open_stops = [to for to in trip.trip_orders if to.order.status != "erledigt"]
    if open_stops:
        raise HTTPException(status_code=409, detail="Nicht alle Stopps sind erledigt")

    trip.status = "abgeschlossen"
    db.add(StatusLog(entity_type="trip", entity_id=trip.id, old_status="aktiv", new_status="abgeschlossen", changed_by=current_user.id))
    await db.commit()

    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    return out


@router.post("/{trip_id}/calculate_route", response_model=TripOut)
async def calculate_route(
    trip_id: uuid.UUID,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    config = await db.get(AppConfig, 1)
    if not config or not config.routing_api_key:
        raise HTTPException(status_code=409, detail="Kein Routing-API-Key konfiguriert")

    try:
        await calculate_route_for_trip(trip, config, db)
        await db.commit()
    except Exception as exc:
        trip.estimated_duration_minutes = None
        if not trip.start_time_manual_override:
            trip.planned_start_time = None
        await db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    return out


class AddOrderBody(BaseModel):
    order_id: uuid.UUID


@router.post("/{trip_id}/add_order", response_model=TripOut)
async def add_order_to_active_trip(
    trip_id: uuid.UUID,
    body: AddOrderBody,
    current_user: DisponentUser,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    if trip.status != "aktiv":
        raise HTTPException(status_code=409, detail="Nur bei aktiven Fahrten möglich")

    existing_ids = {to.order_id for to in trip.trip_orders}
    if body.order_id in existing_ids:
        raise HTTPException(status_code=409, detail="Auftrag ist bereits in dieser Fahrt")

    order = await db.get(Order, body.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
    if order.status != "offen":
        raise HTTPException(status_code=409, detail=f"Auftrag ist nicht offen (Status: {order.status})")

    next_sort = max((to.sort_order for to in trip.trip_orders), default=0) + 1
    db.add(TripOrder(trip_id=trip.id, order_id=order.id, sort_order=next_sort))

    order.status = "unterwegs"
    db.add(StatusLog(entity_type="order", entity_id=order.id, old_status="offen", new_status="unterwegs", changed_by=current_user.id))

    await db.commit()
    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    await broadcaster.broadcast("order_updated", OrderOut.model_validate(order).model_dump())

    if not trip.start_time_manual_override:
        config = await db.get(AppConfig, 1)
        if config and config.routing_api_key and config.routing_mode == "auto":
            try:
                await calculate_route_for_trip(trip, config, db)
                await db.commit()
                trip = await _load_trip(db, trip_id)
                out = TripOut.from_orm_trip(trip)
                await broadcaster.broadcast("trip_updated", out.model_dump())
            except Exception as exc:
                logger.warning("Routenberechnung fehlgeschlagen (trip %s): %s", trip_id, exc)

    return out


@router.post("/{trip_id}/abort", response_model=TripOut)
async def abort_trip(
    trip_id: uuid.UUID,
    current_user: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    trip = await _load_trip(db, trip_id)
    if trip.status not in ("geplant", "aktiv"):
        raise HTTPException(status_code=409, detail="Fahrt kann nicht abgebrochen werden")

    old_trip_status = trip.status
    trip.status = "abgebrochen"
    db.add(StatusLog(entity_type="trip", entity_id=trip.id, old_status=old_trip_status, new_status="abgebrochen", changed_by=current_user.id))

    for to in trip.trip_orders:
        if to.order.status != "erledigt":
            old = to.order.status
            to.order.status = "offen"
            db.add(StatusLog(entity_type="order", entity_id=to.order.id, old_status=old, new_status="offen", changed_by=current_user.id))

    await db.commit()

    trip = await _load_trip(db, trip_id)
    out = TripOut.from_orm_trip(trip)
    await broadcaster.broadcast("trip_updated", out.model_dump())
    for to in trip.trip_orders:
        if to.order.status == "offen":
            await broadcaster.broadcast("order_updated", OrderOut.model_validate(to.order).model_dump())
    return out


@router.get("/{trip_id}/printout")
async def get_printout(
    trip_id: uuid.UUID,
    _: DisponentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models import AppConfig
    from app.schemas.config import AppConfigOut

    trip = await _load_trip(db, trip_id)
    config = await db.get(AppConfig, 1)

    return {
        "trip": TripOut.from_orm_trip(trip).model_dump(),
        "config": AppConfigOut.model_validate(config).model_dump() if config else {},
    }
