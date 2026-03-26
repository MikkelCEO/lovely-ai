const callsEl = document.getElementById("calls");
const activeCallsEl = document.getElementById("activeCalls");
const messageCountEl = document.getElementById("messageCount");
const lastUpdateEl = document.getElementById("lastUpdate");
const statusTextEl = document.getElementById("statusText");
const statusDotEl = document.getElementById("statusDot");
const refreshBtn = document.getElementById("refreshBtn");
const callTemplate = document.getElementById("callTemplate");
const messageTemplate = document.getElementById("messageTemplate");

let pollHandle = null;

function setStatus(text, online) {
    statusTextEl.textContent = text;
    statusDotEl.classList.toggle("online", !!online);
    statusDotEl.classList.toggle("offline", !online);
}

function formatTime(date) {
    return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function getRoleLabel(role) {
    if (role === "user") return "Caller";
    if (role === "assistant") return "Assistant";
    if (role === "system") return "System";
    return role || "Unknown";
}

function renderEmpty() {
    callsEl.innerHTML = `
        <div class="empty-state">
            <div class="empty-title">No active calls</div>
            <div class="empty-text">When a call starts, messages will appear here live.</div>
        </div>
    `;
}

function renderCalls(data) {
    const entries = Object.entries(data || {});
    const totalMessages = entries.reduce((sum, [, messages]) => sum + messages.length, 0);

    activeCallsEl.textContent = String(entries.length);
    messageCountEl.textContent = String(totalMessages);
    lastUpdateEl.textContent = formatTime(new Date());

    if (entries.length === 0) {
        renderEmpty();
        return;
    }

    callsEl.innerHTML = "";

    for (const [callId, messages] of entries) {
        const callNode = callTemplate.content.firstElementChild.cloneNode(true);
        callNode.querySelector(".call-title").textContent = callId;
        callNode.querySelector(".call-subtitle").textContent = `${messages.length} message${messages.length === 1 ? "" : "s"}`;

        const messagesEl = callNode.querySelector(".messages");

        for (const msg of messages) {
            const msgNode = messageTemplate.content.firstElementChild.cloneNode(true);
            const role = msg.role || "unknown";
            msgNode.classList.add(`role-${role}`);

            msgNode.querySelector(".message-meta").textContent = getRoleLabel(role);
            msgNode.querySelector(".message-content").innerHTML = escapeHtml(msg.content || "").replaceAll("\n", "<br>");

            messagesEl.appendChild(msgNode);
        }

        callsEl.appendChild(callNode);
    }
}

async function loadDashboard() {
    try {
        const res = await fetch("/dashboard/data", { cache: "no-store" });
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        renderCalls(data);
        setStatus("Live", true);
    } catch (error) {
        setStatus("Offline", false);
        callsEl.innerHTML = `
            <div class="empty-state error-state">
                <div class="empty-title">Dashboard unavailable</div>
                <div class="empty-text">${escapeHtml(error.message)}</div>
            </div>
        `;
    }
}

refreshBtn.addEventListener("click", loadDashboard);

loadDashboard();
pollHandle = setInterval(loadDashboard, 1000);