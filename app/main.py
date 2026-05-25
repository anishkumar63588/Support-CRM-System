from datetime import datetime

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="app/templates")


def next_ticket_id(db: Session) -> str:
    last_ticket = db.query(Ticket).order_by(Ticket.id.desc()).first()
    next_number = 1 if last_ticket is None else last_ticket.id + 1
    return f"TKT-{next_number:03d}"


def build_ticket_query(db: Session, status: str | None = None, search: str | None = None):
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

    return query.order_by(Ticket.created_at.desc())


def create_ticket_record(db: Session, payload: TicketCreate) -> Ticket:
    ticket = Ticket(
        ticket_id=next_ticket_id(db),
        customer_name=payload.customer_name.strip(),
        customer_email=payload.customer_email.strip().lower(),
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        status="Open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


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


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    status: TicketStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    created: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    tickets = build_ticket_query(db, status=status, search=search).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tickets": tickets,
            "selected_status": status or "",
            "search": search or "",
            "created": created,
        },
    )


@app.post("/tickets")
def create_ticket_from_form(
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    subject: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    payload = TicketCreate(
        customer_name=customer_name,
        customer_email=customer_email,
        subject=subject,
        description=description,
    )
    ticket = create_ticket_record(db, payload)
    return RedirectResponse(
        url=f"/?created={ticket.ticket_id}",
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_page(request: Request, ticket_id: str, db: Session = Depends(get_db)):
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.notes))
        .filter(Ticket.ticket_id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "ticket": ticket,
            "notes": sorted(ticket.notes, key=lambda note: note.created_at, reverse=True),
            "updated": request.query_params.get("updated"),
        },
    )


@app.post("/tickets/{ticket_id}")
def update_ticket_from_form(
    ticket_id: str,
    status: TicketStatus = Form(...),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    ticket.updated_at = datetime.utcnow()

    if notes and notes.strip():
        db.add(Note(ticket_id=ticket.id, note_text=notes.strip()))

    db.commit()
    return RedirectResponse(
        url=f"/tickets/{ticket.ticket_id}?updated=1",
        status_code=http_status.HTTP_303_SEE_OTHER,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/tickets", response_model=TicketCreateResponse, status_code=201)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    return create_ticket_record(db, payload)


@app.get("/api/tickets", response_model=list[TicketListItem])
def list_tickets(
    status: TicketStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return build_ticket_query(db, status=status, search=search).all()


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
