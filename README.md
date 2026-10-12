Mini Autonomous Travel Agent

A classroom-ready mini autonomous AI travel agent built with a **Flask backend** and a **HTML/CSS/JavaScript frontend**.

This project demonstrates the complete agent lifecycle required for **Class Activity 3**:

> Goal → LLM → Memory → Planning → Reasoning → Tools → Actions → Observations → Re-planning → Human Approval

The project uses a deterministic simulated travel database, so it works without external airline/hotel APIs.

---

## 1. Features

- Natural-language travel request input
- Simple request understanding layer
- Persistent JSON memory
- Autonomous planning
- Reasoning over tool results
- Flight search tool
- Hotel search tool
- Weather tool
- Observation logging
- Automatic re-planning when the first flight search fails
- Human-in-the-loop approval
- Booking action is blocked unless the user explicitly approves
- Clean browser-based frontend
- Flask REST API backend

---

## 2. Project Structure

```text
mini-autonomous-travel-agent/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── travel_memory.json
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── docs/
│   └── architecture.md
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## 3. Agent Architecture

```text
                         ┌──────────────────┐
                         │   USER REQUEST   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │       LLM        │
                         │   Understand     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      MEMORY      │
                         │ Preferences /    │
                         │ Previous trips   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      PLANNER     │
                         │ Constraints +    │
                         │ tool selection   │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │          TOOLS              │
                    │ Flights │ Hotels │ Weather  │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                         │   OBSERVATIONS   │
                         │ Tool results     │
                         └────────┬─────────┘
                                  │
                         Failure?
                          /       \
                        YES        NO
                        │           │
                        ▼           ▼
                 ┌────────────┐ ┌─────────────┐
                 │ RE-PLANNING│ │ FINAL PLAN  │
                 └─────┬──────┘ └──────┬──────┘
                       │               │
                       └───────┬───────┘
                               ▼
                       ┌───────────────┐
                       │ HUMAN APPROVAL│
                       └───────┬───────┘
                               │
                         Approved?
                          /     \
                        NO       YES
                        │         │
                        ▼         ▼
                       STOP    ACTION
                                  │
                                  ▼
                                MEMORY
```

---

## 4. Agent Components

| Component | Implementation |
|---|---|
| Goal | Create a travel plan within the user's budget |
| LLM | Request-understanding and plan-selection layer |
| Memory | `backend/travel_memory.json` |
| Planning | Budget allocation and tool selection |
| Reasoning | Selects feasible flight/hotel using tool observations |
| Tools | Flights, hotels, weather, booking |
| Actions | Prepare and authorize demo booking |
| Observations | Every tool result is recorded |
| Re-planning | Flight search limit is increased by 20% when initial search fails |
| Human approval | Final booking action requires explicit approval |

---

## 5. Tools

### `search_flights`

Searches the simulated flight database.

```text
search_flights(source, destination, date, max_price)
```

### `search_hotels`

Searches the simulated hotel database.

```text
search_hotels(destination, date, max_price_per_night)
```

### `get_weather`

Returns destination weather.

```text
get_weather(destination, date)
```

### `create_booking_request`

The final action is protected by human approval in the UI/API.

---

## 6. Memory Design

Memory is stored in:

```text
backend/travel_memory.json
```

It contains:

```json
{
  "traveler": {
    "preferred_transport": "flight",
    "preferred_hotel_type": "3-star",
    "preferences": []
  },
  "past_trips": []
}
```

After an approved booking, the trip is added to `past_trips`.

---

## 7. Agent Lifecycle

```text
1. Receive travel request
2. Understand request
3. Load memory
4. Create initial plan
5. Search flights
6. Observe flight results
7. Search hotels
8. Observe hotel results
9. Get weather
10. Observe weather
11. Reason about available options
12. If necessary, re-plan
13. Create final plan
14. Ask human for approval
15. If rejected → stop
16. If approved → execute demo booking
17. Update memory
```

---

## 8. Failure / Re-planning Example

Use:

```text
Plan a trip from Bangalore to Delhi within 8000
```

The agent initially allocates about 65% of the budget to the flight:

```text
₹8000 × 0.65 = ₹5200
```

The cheapest matching demo flight costs ₹5800.

Therefore:

```text
Initial search
      ↓
No flight under ₹5200
      ↓
Observation: search failed
      ↓
Re-planning
      ↓
Increase flight limit by 20%
      ↓
₹5200 × 1.20 = ₹6240
      ↓
Search again
      ↓
6E202 found for ₹5800
```

The agent then continues with hotel and weather tools and can produce a plan.

---

## 9. Successful Execution

Example request:

```text
Plan a trip from Bangalore to Delhi within 10000
```

The agent can produce:

```text
Flight: 6E202
Price: ₹5800

Hotel: City Comfort Hotel
Price: ₹2200/night

Weather: Sunny, 29°C

Total demo cost: ₹8000
```

The frontend then asks:

```text
Approve & Book
```

Only after the user clicks the approval button is the booking action executed.

---

## 10. Human-in-the-Loop Safety Rule

> The agent may search, compare, reason, and prepare a booking, but it must not execute the final booking action without explicit human approval.

If the user rejects the booking:

```text
No booking is made.
```

This prevents an autonomous agent from performing an external side effect without authorization.

---

## 11. How to Run

### Step 1 — Install Python

Python 3.10+ is recommended.

### Step 2 — Open the project

```bash
cd mini-autonomous-travel-agent
```

### Step 3 — Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 5 — Start the backend

```bash
python backend/app.py
```

You should see Flask running on:

```text
http://127.0.0.1:5000
```

### Step 6 — Open the application

Open:

```text
http://127.0.0.1:5000
```

---

## 12. Demo Buttons

The frontend includes:

### Successful demo

Uses:

```text
Plan a trip from Bangalore to Delhi within 10000
```

### Re-planning demo

Uses:

```text
Plan a trip from Bangalore to Delhi within 8000
```

The second example demonstrates the autonomous recovery/re-planning behavior.

---

## 13. API Endpoints

### Health check

```http
GET /api/health
```

### Read memory

```http
GET /api/memory
```

### Create travel plan

```http
POST /api/plan
Content-Type: application/json

{
  "request": "Plan a trip from Bangalore to Delhi within 10000"
}
```

### Approve booking

```http
POST /api/approve
Content-Type: application/json

{
  "plan": { ... }
}
```

### Reject booking

```http
POST /api/reject
Content-Type: application/json

{
  "plan": { ... }
}
```

---

## 14. Important Note

This is an **educational prototype**. Flight, hotel, weather and booking data are simulated.

No real airline, hotel or payment transaction is performed.

The project is intentionally designed this way so the agent architecture and autonomous lifecycle can be demonstrated safely without real-world side effects.

---

## 15. Future Improvements

Possible extensions:

- Connect a real LLM
- Connect real flight/hotel APIs
- Add date extraction
- Add multiple destinations
- Add user authentication
- Add a real database
- Add price comparison
- Add cancellation handling
- Add tool failure handling
- Add richer long-term memory
- Add real-time weather
- Add email itinerary generation
=======
# TravelAgent
A mini Autonomous AI travel agent
>>>>>>> 6059de3482784b37c31485c5bda33e1ad7eac783
