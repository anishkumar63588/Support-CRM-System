const ticketId = window.location.pathname.split("/").filter(Boolean).pop();
const updateForm = document.querySelector("#update-form");
const updateNotice = document.querySelector("#update-notice");

const formatDate = (value) =>
  new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));

const statusClass = (status) => status.toLowerCase().replaceAll(" ", "-");

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);

const showNotice = (message, type) => {
  updateNotice.textContent = message;
  updateNotice.className = `notice show ${type}`;
};

function renderNotes(notes) {
  const notesContainer = document.querySelector("#notes");
  if (!notes.length) {
    notesContainer.innerHTML = '<p class="muted">No notes yet.</p>';
    return;
  }

  notesContainer.innerHTML = notes
    .map(
      (note) => `
        <div class="note">
          <p>${escapeHtml(note.note_text)}</p>
          <small class="muted">${formatDate(note.created_at)}</small>
        </div>
      `
    )
    .join("");
}

async function loadTicket() {
  const response = await fetch(`/api/tickets/${ticketId}`);
  if (!response.ok) {
    document.querySelector("#subject").textContent = "Ticket not found";
    return;
  }

  const ticket = await response.json();
  document.title = `${ticket.ticket_id} - Support CRM`;
  document.querySelector("#ticket-heading").textContent = ticket.ticket_id;
  document.querySelector("#ticket-subtitle").textContent = ticket.subject;
  document.querySelector("#subject").textContent = ticket.subject;
  document.querySelector("#customer-name").textContent = ticket.customer_name;
  document.querySelector("#customer-email").textContent = ticket.customer_email;
  document.querySelector("#current-status").innerHTML =
    `<span class="status ${statusClass(ticket.status)}">${ticket.status}</span>`;
  document.querySelector("#created-at").textContent = formatDate(ticket.created_at);
  document.querySelector("#description").textContent = ticket.description;
  document.querySelector("#status").value = ticket.status;
  renderNotes(ticket.notes);
}

updateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(updateForm).entries());

  const response = await fetch(`/api/tickets/${ticketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    showNotice("Could not update the ticket.", "error");
    return;
  }

  updateForm.elements.notes.value = "";
  showNotice("Ticket updated.", "success");
  await loadTicket();
});

loadTicket();
