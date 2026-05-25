const ticketList = document.querySelector("#ticket-list");
const searchInput = document.querySelector("#search");
const statusSelect = document.querySelector("#status");
const ticketForm = document.querySelector("#ticket-form");
const formNotice = document.querySelector("#form-notice");

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

const showNotice = (element, message, type) => {
  element.textContent = message;
  element.className = `notice show ${type}`;
};

let searchTimer;

async function loadTickets() {
  const params = new URLSearchParams();
  if (searchInput.value.trim()) params.set("search", searchInput.value.trim());
  if (statusSelect.value) params.set("status", statusSelect.value);

  const response = await fetch(`/api/tickets?${params.toString()}`);
  const tickets = await response.json();

  ticketList.innerHTML = `
    <div class="ticket-row header">
      <span>ID</span>
      <span>Name</span>
      <span class="subject">Title</span>
      <span>Status</span>
      <span class="date">Date</span>
    </div>
  `;

  if (!tickets.length) {
    ticketList.insertAdjacentHTML("beforeend", '<div class="empty">No tickets found.</div>');
    return;
  }

  for (const ticket of tickets) {
    ticketList.insertAdjacentHTML(
      "beforeend",
      `
        <a class="ticket-row" href="/tickets/${ticket.ticket_id}">
          <span class="ticket-id">${ticket.ticket_id}</span>
          <span class="truncate">${escapeHtml(ticket.customer_name)}</span>
          <span class="subject truncate">${escapeHtml(ticket.subject)}</span>
          <span class="status ${statusClass(ticket.status)}">${ticket.status}</span>
          <span class="date muted">${formatDate(ticket.created_at)}</span>
        </a>
      `
    );
  }
}

searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadTickets, 180);
});

statusSelect.addEventListener("change", loadTickets);

ticketForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(ticketForm).entries());

  const response = await fetch("/api/tickets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    showNotice(formNotice, "Could not create the ticket. Please check the form.", "error");
    return;
  }

  const created = await response.json();
  ticketForm.reset();
  showNotice(formNotice, `Created ${created.ticket_id}.`, "success");
  await loadTickets();
});

loadTickets().catch(() => {
  ticketList.innerHTML = '<div class="empty">Unable to load tickets.</div>';
});
