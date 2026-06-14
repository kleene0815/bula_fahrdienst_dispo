from pydantic import BaseModel


class AppConfigOut(BaseModel):
    printout_header_html: str
    default_deadline_time: str

    model_config = {"from_attributes": True}


class AppConfigUpdate(BaseModel):
    printout_header_html: str
    default_deadline_time: str
