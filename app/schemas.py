from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


TicketStatus = Literal["Open", "In Progress", "Closed"]


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    customer_email: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1)

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Enter a valid email address")
        return email


class TicketCreateResponse(BaseModel):
    ticket_id: str
    created_at: datetime


class TicketListItem(BaseModel):
    ticket_id: str
    customer_name: str
    subject: str
    status: str
    created_at: datetime


class NoteResponse(BaseModel):
    id: int
    note_text: str
    created_at: datetime


class TicketDetail(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    notes: list[NoteResponse]


class TicketUpdate(BaseModel):
    status: TicketStatus
    notes: str | None = Field(default=None)


class TicketUpdateResponse(BaseModel):
    success: bool
    updated_at: datetime
