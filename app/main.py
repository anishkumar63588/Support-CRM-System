from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import Base, engine, get_db
from app.models import Note, Ticket
from app.schemas import (
    TicketCreate,
    TicketCreateResponse,
    TicketDetail,
    TicketListItem,
    TicketStatus,
    TicketUpdate,
    TicketUpdateResponse,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Support CRM System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def next_ticket_id(db: Session) -> str:
    last_ticket = db.query(Ticket).order_by(Ticket.id.desc()).first()
    next_number = 1 if last_ticket is None else last_ticket.id + 1
    return f"TKT-{next_number:03d}"


def serialize_ticket(ticket: Ticket) -> TicketDetail:
    return TicketDetail(
        ticket_id=ticket.ticket_id,
        customer_name=ticket.customer_name,
        customer_email=ticket.customer_email,
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        notes=[
            {"id": note.id, "note_text": note.note_text, "created_at": note.created_at}
            for note in sorted(ticket.notes, key=lambda item: item.created_at, reverse=True)
        ],
    )


@app.get("/")
def home():
    return FileResponse("app/static/index.html")


@app.get("/tickets/{ticket_id}")
def ticket_page(ticket_id: str):
    return FileResponse("app/static/detail.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/tickets", response_model=TicketCreateResponse, status_code=201)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(
        ticket_id=next_ticket_id(db),
        customer_name=payload.customer_name.strip(),
        customer_email=str(payload.customer_email).strip().lower(),
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        status="Open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/api/tickets", response_model=list[TicketListItem])
def list_tickets(
    status: TicketStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Ticket.ticket_id.ilike(term),
                Ticket.customer_name.ilike(term),
                Ticket.customer_email.ilike(term),
                Ticket.subject.ilike(term),
                Ticket.description.ilike(term),
            )
        )

    return query.order_by(Ticket.created_at.desc()).all()


@app.get("/api/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.notes))
        .filter(Ticket.ticket_id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return serialize_ticket(ticket)


@app.put("/api/tickets/{ticket_id}", response_model=TicketUpdateResponse)
def update_ticket(ticket_id: str, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = payload.status
    ticket.updated_at = datetime.utcnow()

    if payload.notes and payload.notes.strip():
        db.add(Note(ticket_id=ticket.id, note_text=payload.notes.strip()))

    db.commit()
    db.refresh(ticket)
    return {"success": True, "updated_at": ticket.updated_at}
