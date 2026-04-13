from pydantic import BaseModel


class AppConfigOut(BaseModel):
    security_center_name: str
    security_center_phone: str
    organizer_name: str
    camp_address: str
    default_deadline_time: str

    model_config = {"from_attributes": True}


class AppConfigUpdate(BaseModel):
    security_center_name: str
    security_center_phone: str
    organizer_name: str
    camp_address: str
    default_deadline_time: str
