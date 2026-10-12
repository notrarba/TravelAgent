const requestInput = document.getElementById("requestInput");
const planBtn = document.getElementById("planBtn");
const timeline = document.getElementById("timeline");
const planPanel = document.getElementById("planPanel");
const memoryOutput = document.getElementById("memoryOutput");
const statusPill = document.getElementById("statusPill");
const toast = document.getElementById("toast");

let currentPlan = null;

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2800);
}

function setStatus(text, active = true) {
    statusPill.innerHTML = `<span class="dot"></span> ${text}`;
    if (!active) {
        statusPill.querySelector(".dot").style.background = "var(--warning)";
    }
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderTimeline(steps) {
    if (!steps || steps.length === 0) {
        timeline.className = "timeline empty-state";
        timeline.textContent = "No lifecycle information.";
        return;
    }

    timeline.className = "timeline";

    timeline.innerHTML = steps.map((step, index) => {
        const icon = {
            goal: "G",
            memory: "M",
            planning: "P",
            tool: "T",
            replan: "↻",
            reasoning: "R",
            plan: "✓",
            failure: "!"
        }[step.type] || (index + 1);

        return `
            <div class="step ${step.type}">
                <div class="step-icon">${icon}</div>
                <div>
                    <div class="step-title">${escapeHtml(step.type.toUpperCase())}</div>
                    <div class="step-message">${escapeHtml(step.message)}</div>
                </div>
            </div>
        `;
    }).join("");
}

function renderPlan(result) {
    if (!result.success || !result.plan) {
        planPanel.className = "plan-panel empty-state";
        planPanel.textContent =
            "The agent could not create a feasible plan. Check the lifecycle for the failure/re-planning details.";
        currentPlan = null;
        return;
    }

    currentPlan = result.plan;

    const f = result.plan.flight;
    const h = result.plan.hotel;
    const w = result.plan.weather;

    planPanel.className = "plan-panel";

    planPanel.innerHTML = `
        <div class="plan-card">
            <h3>✈ Flight</h3>
            <p><strong>${escapeHtml(f.id)}</strong> · ${escapeHtml(f.source)} → ${escapeHtml(f.destination)}</p>
            <p>${escapeHtml(f.date)} · ${escapeHtml(f.departure)} – ${escapeHtml(f.arrival)}</p>
            <div class="price">₹${Number(f.price).toLocaleString("en-IN")}</div>
        </div>

        <div class="plan-card">
            <h3>🏨 Hotel</h3>
            <p><strong>${escapeHtml(h.name)}</strong></p>
            <p>${escapeHtml(h.type)} · Rating ${escapeHtml(h.rating)}</p>
            <div class="price">₹${Number(h.price).toLocaleString("en-IN")} / night</div>
        </div>

        <div class="plan-card">
            <h3>🌤 Destination weather</h3>
            <span class="weather">
                ${escapeHtml(w.condition)} · ${escapeHtml(w.temperature_c)}°C · ${escapeHtml(w.rain_probability)}% rain
            </span>
        </div>

        <div class="plan-card">
            <strong>Total demo cost</strong>
            <div class="price">₹${Number(result.plan.total).toLocaleString("en-IN")}</div>
            <p>Final booking action requires explicit human approval.</p>
            <div class="approval">
                <button class="approve" id="approveBtn">Approve & Book</button>
                <button class="reject" id="rejectBtn">Reject</button>
            </div>
        </div>
    `;

    document.getElementById("approveBtn").addEventListener("click", approveBooking);
    document.getElementById("rejectBtn").addEventListener("click", rejectBooking);
}

async function buildPlan() {
    const userRequest = requestInput.value.trim();

    if (!userRequest) {
        showToast("Please enter a travel request.");
        return;
    }

    planBtn.disabled = true;
    planBtn.textContent = "Planning...";
    setStatus("Agent working...", true);
    timeline.className = "timeline empty-state";
    timeline.textContent = "Calling tools and observing results...";
    planPanel.className = "plan-panel empty-state";
    planPanel.textContent = "Building a feasible plan...";

    try {
        const response = await fetch("/api/plan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ request: userRequest })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not create plan.");
        }

        renderTimeline(result.steps);
        renderPlan(result);

        setStatus(
            result.success
                ? (result.replanned ? "Plan ready · re-planned" : "Plan ready")
                : "Planning failed",
            result.success
        );

        if (result.replanned) {
            showToast("The agent detected a constraint failure and re-planned.");
        }
    } catch (error) {
        setStatus("Connection error", false);
        timeline.className = "timeline empty-state";
        timeline.textContent = error.message;
        planPanel.className = "plan-panel empty-state";
        planPanel.textContent = "Backend connection failed.";
        showToast(error.message);
    } finally {
        planBtn.disabled = false;
        planBtn.textContent = "Build Plan";
    }
}

async function approveBooking() {
    if (!currentPlan) return;

    const button = document.getElementById("approveBtn");
    button.disabled = true;
    button.textContent = "Authorizing...";

    try {
        const response = await fetch("/api/approve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ plan: currentPlan })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Approval failed.");
        }

        setStatus("Action completed", true);
        showToast("Human approval recorded. Demo booking completed.");
        await loadMemory();

        button.textContent = "✓ Booking completed";
    } catch (error) {
        button.disabled = false;
        button.textContent = "Approve & Book";
        showToast(error.message);
    }
}

async function rejectBooking() {
    try {
        await fetch("/api/reject", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ plan: currentPlan })
        });

        setStatus("Action blocked", false);
        showToast("Booking rejected. No action was taken.");
    } catch (error) {
        showToast(error.message);
    }
}

async function loadMemory() {
    try {
        const response = await fetch("/api/memory");
        const memory = await response.json();
        memoryOutput.textContent = JSON.stringify(memory, null, 2);
    } catch (error) {
        memoryOutput.textContent = "Could not load memory.";
    }
}

document.getElementById("planBtn").addEventListener("click", buildPlan);

requestInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        buildPlan();
    }
});

document.getElementById("successDemo").addEventListener("click", () => {
    requestInput.value =
        "Plan a trip from Bangalore to Delhi within 10000";
    buildPlan();
});

document.getElementById("replanDemo").addEventListener("click", () => {
    requestInput.value =
        "Plan a trip from Bangalore to Delhi within 8000";
    buildPlan();
});

document.getElementById("memoryBtn").addEventListener("click", loadMemory);

loadMemory();
