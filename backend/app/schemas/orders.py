import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


class OrderCreate(BaseModel):
    trip_type: str
    destination_type: str
    destination: str
    destination_address: str | None = None
    deadline: datetime
    priority: str = "gering"
    patient_name: str | None = None
    phone: str | None = None
    companion: bool = False
    notes: str | None = None
    requester_station: str | None = None

    @model_validator(mode="after")
    def companion_requires_patient(self):
        if self.companion and not self.patient_name:
            raise ValueError("Begleitperson erfordert einen Patientennamen")
        return self


class OrderUpdate(BaseModel):
    trip_type: str | None = None
    destination_type: str | None = None
    destination: str | None = None
    destination_address: str | None = None
    deadline: datetime | None = None
    priority: str | None = None
    patient_name: str | None = None
    phone: str | None = None
    companion: bool | None = None
    notes: str | None = None
    requester_station: str | None = None


class OrderOut(BaseModel):
    id: uuid.UUID
    status: str
    priority: str
    trip_type: str
    destination: str
    destination_address: str | None
    destination_type: str
    deadline: datetime
    patient_name: str | None
    phone: str | None
    companion: bool
    notes: str | None
    requester_station: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
