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

    def to_db_dict(self) -> dict:
        return {
            "printout_header_html": self.printout_header_html,
            "default_deadline_time": self.default_deadline_time,
            "destination_suggestions": json.dumps(
                [s.model_dump() for s in self.destination_suggestions],
                ensure_ascii=False,
            ),
        }
