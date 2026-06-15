import json

from pydantic import BaseModel, field_validator, model_serializer


class DestinationSuggestion(BaseModel):
    name: str
    street: str
    city: str


class AppConfigOut(BaseModel):
    printout_header_html: str
    default_deadline_time: str
    destination_suggestions: list[DestinationSuggestion]
    camp_address: str
    routing_api_key: str | None
    routing_mode: str
    routing_remaining_requests: int | None
    stop_duration_hinfahrt: int
    stop_duration_abholung: int
    stop_duration_besorgung: int

    model_config = {"from_attributes": True}

    @field_validator("destination_suggestions", mode="before")
    @classmethod
    def parse_suggestions(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v


class AppConfigUpdate(BaseModel):
    printout_header_html: str
    default_deadline_time: str
    destination_suggestions: list[DestinationSuggestion]
    camp_address: str
    routing_api_key: str | None = None
    routing_mode: str
    stop_duration_hinfahrt: int
    stop_duration_abholung: int
    stop_duration_besorgung: int

    def to_db_dict(self) -> dict:
        return {
            "printout_header_html": self.printout_header_html,
            "default_deadline_time": self.default_deadline_time,
            "destination_suggestions": json.dumps(
                [s.model_dump() for s in self.destination_suggestions],
                ensure_ascii=False,
            ),
            "camp_address": self.camp_address,
            "routing_api_key": self.routing_api_key,
            "routing_mode": self.routing_mode,
            "stop_duration_hinfahrt": self.stop_duration_hinfahrt,
            "stop_duration_abholung": self.stop_duration_abholung,
            "stop_duration_besorgung": self.stop_duration_besorgung,
        }
