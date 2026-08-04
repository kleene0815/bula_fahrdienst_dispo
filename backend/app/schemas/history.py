from datetime import datetime

from pydantic import BaseModel


class HistoryEntryOut(BaseModel):
    old_status: str | None
    new_status: str
    changed_by_name: str
    changed_at: datetime
    note: str | None
    # Gesetzt bei Auftrags-Einträgen in der Fahrt-Historie (Ziel des erledigten Auftrags)
    destination: str | None = None

    model_config = {"from_attributes": True}
