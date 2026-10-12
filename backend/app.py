from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
MEMORY_FILE = BASE_DIR / "travel_memory.json"

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)


# -----------------------------
# Persistent memory
# -----------------------------

def default_memory():
    return {
        "traveler": {
            "preferred_transport": "flight",
            "preferred_hotel_type": "3-star",
            "preferences": []
        },
        "past_trips": []
    }


def load_memory():
    if not MEMORY_FILE.exists():
        return default_memory()

    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_memory()


def save_memory(memory):
    MEMORY_FILE.write_text(
        json.dumps(memory, indent=2),
        encoding="utf-8"
    )


# -----------------------------
# Simulated travel tools
# -----------------------------

def search_flights(source, destination, date, max_price):
    flights = [
        {
            "id": "AI101",
            "source": "Bangalore",
            "destination": "Delhi",
            "date": "2026-10-10",
            "price": 6200,
            "departure": "08:00",
            "arrival": "10:45"
        },
        {
            "id": "6E202",
            "source": "Bangalore",
            "destination": "Delhi",
            "date": "2026-10-10",
            "price": 5800,
            "departure": "14:00",
            "arrival": "16:40"
        },
        {
            "id": "UK303",
            "source": "Bangalore",
            "destination": "Delhi",
            "date": "2026-10-10",
            "price": 7100,
            "departure": "18:30",
            "arrival": "21:15"
        }
    ]

    matches = [
        f for f in flights
        if f["source"].lower() == source.lower()
        and f["destination"].lower() == destination.lower()
        and f["date"] == date
        and f["price"] <= max_price
    ]

    return matches


def search_hotels(destination, date, max_price_per_night):
    hotels = [
        {
            "id": "H101",
            "name": "City Comfort Hotel",
            "city": "Delhi",
            "date": "2026-10-10",
            "price": 2200,
            "rating": 4.1,
            "type": "3-star"
        },
        {
            "id": "H102",
            "name": "Metro Stay",
            "city": "Delhi",
            "date": "2026-10-10",
            "price": 1800,
            "rating": 4.0,
            "type": "3-star"
        }
    ]

    return [
        h for h in hotels
        if h["city"].lower() == destination.lower()
        and h["date"] == date
        and h["price"] <= max_price_per_night
    ]


def get_weather(destination, date):
    weather = {
        ("delhi", "2026-10-10"): {
            "condition": "Sunny",
            "temperature_c": 29,
            "rain_probability": 10
        }
    }

    return weather.get(
        (destination.lower(), date),
        {
            "condition": "Partly cloudy",
            "temperature_c": 27,
            "rain_probability": 20
        }
    )


# -----------------------------
# Simple request understanding
# -----------------------------

def understand_request(text):
    """
    Lightweight parser for the classroom demo.

    The app accepts natural language such as:
    "Plan a trip from Bangalore to Delhi for 10000"
    """

    lower = text.lower()

    source = "Bangalore"
    destination = "Delhi"
    budget = 10000
    date = "2026-10-10"
    travelers = 1

    if "mumbai" in lower:
        destination = "Mumbai"

    if "bangalore" in lower or "bengaluru" in lower:
        source = "Bangalore"

    for amount in (15000, 12000, 10000, 8000):
        if str(amount) in lower:
            budget = amount
            break

    return {
        "source": source,
        "destination": destination,
        "date": date,
        "budget": budget,
        "travelers": travelers
    }


# -----------------------------
# Autonomous agent
# -----------------------------

class TravelAgent:
    def __init__(self):
        self.observations = []
        self.plan_history = []

    def observe(self, tool_name, result):
        observation = {
            "tool": tool_name,
            "result": result
        }
        self.observations.append(observation)
        return observation

    def run(self, user_request):
        parsed = understand_request(user_request)
        memory = load_memory()

        source = parsed["source"]
        destination = parsed["destination"]
        date = parsed["date"]
        budget = parsed["budget"]

        steps = []

        steps.append({
            "type": "goal",
            "message": (
                f"Goal: plan a trip from {source} to {destination} "
                f"on {date} within ₹{budget:,}."
            )
        })

        steps.append({
            "type": "memory",
            "message": "Loaded persistent traveler memory.",
            "data": memory
        })

        # Planning
        initial_flight_limit = int(budget * 0.65)
        hotel_limit = int(budget * 0.35)

        steps.append({
            "type": "planning",
            "message": (
                f"Initial plan: search for flights up to "
                f"₹{initial_flight_limit:,} and hotels up to "
                f"₹{hotel_limit:,}/night."
            )
        })

        # Tool: flights
        flights = search_flights(
            source,
            destination,
            date,
            initial_flight_limit
        )

        self.observe("search_flights", flights)
        steps.append({
            "type": "tool",
            "tool": "search_flights",
            "message": f"Found {len(flights)} flight(s).",
            "data": flights
        })

        # Re-planning if the first search fails
        replanned = False
        if not flights:
            replanned = True
            new_limit = int(initial_flight_limit * 1.20)

            steps.append({
                "type": "replan",
                "message": (
                    "No flight matched the initial constraint. "
                    f"Re-planning with a new flight limit of ₹{new_limit:,}."
                )
            })

            flights = search_flights(
                source,
                destination,
                date,
                new_limit
            )

            self.observe("search_flights_replan", flights)
            steps.append({
                "type": "tool",
                "tool": "search_flights_replan",
                "message": f"Re-planning search found {len(flights)} flight(s).",
                "data": flights
            })

        hotels = search_hotels(
            destination,
            date,
            hotel_limit
        )

        self.observe("search_hotels", hotels)
        steps.append({
            "type": "tool",
            "tool": "search_hotels",
            "message": f"Found {len(hotels)} hotel(s).",
            "data": hotels
        })

        weather = get_weather(destination, date)

        self.observe("get_weather", weather)
        steps.append({
            "type": "tool",
            "tool": "get_weather",
            "message": "Retrieved destination weather.",
            "data": weather
        })

        if not flights or not hotels:
            steps.append({
                "type": "failure",
                "message": (
                    "The agent could not create a feasible plan "
                    "with the available demo data."
                )
            })

            return {
                "success": False,
                "replanned": replanned,
                "request": parsed,
                "steps": steps,
                "observations": self.observations
            }

        # Reasoning / selection
        selected_flight = sorted(
            flights,
            key=lambda item: item["price"]
        )[0]

        selected_hotel = sorted(
            hotels,
            key=lambda item: (-item["rating"], item["price"])
        )[0]

        total = selected_flight["price"] + selected_hotel["price"]

        steps.append({
            "type": "reasoning",
            "message": (
                "Reasoning: selected the lowest-price available flight "
                "and a highly rated hotel within the hotel constraint."
            )
        })

        steps.append({
            "type": "plan",
            "message": "A feasible travel plan is ready.",
            "data": {
                "flight": selected_flight,
                "hotel": selected_hotel,
                "weather": weather,
                "total": total
            }
        })

        return {
            "success": True,
            "replanned": replanned,
            "request": parsed,
            "plan": {
                "flight": selected_flight,
                "hotel": selected_hotel,
                "weather": weather,
                "total": total
            },
            "steps": steps,
            "observations": self.observations
        }


agent = TravelAgent()


# -----------------------------
# API routes
# -----------------------------

@app.get("/")
def index():
    return send_from_directory("../frontend", "index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Mini Autonomous Travel Agent"
    })


@app.get("/api/memory")
def get_memory():
    return jsonify(load_memory())


@app.post("/api/plan")
def create_plan():
    body = request.get_json(silent=True) or {}
    user_request = body.get("request", "").strip()

    if not user_request:
        return jsonify({"error": "Travel request is required."}), 400

    result = TravelAgent().run(user_request)
    return jsonify(result)


@app.post("/api/approve")
def approve_booking():
    body = request.get_json(silent=True) or {}
    plan = body.get("plan")

    if not plan:
        return jsonify({"error": "No travel plan was supplied."}), 400

    flight = plan.get("flight")
    hotel = plan.get("hotel")
    total = plan.get("total")

    if not flight or not hotel:
        return jsonify({"error": "Incomplete travel plan."}), 400

    memory = load_memory()

    trip = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": flight["source"],
        "destination": flight["destination"],
        "date": flight["date"],
        "flight": flight["id"],
        "hotel": hotel["name"],
        "total": total
    }

    memory["past_trips"].append(trip)
    memory["traveler"]["preferences"].append(
        f"Travelled from {flight['source']} to {flight['destination']}"
    )

    # Remove duplicates while preserving order.
    memory["traveler"]["preferences"] = list(
        dict.fromkeys(memory["traveler"]["preferences"])
    )

    save_memory(memory)

    return jsonify({
        "success": True,
        "message": "Booking authorized by human and completed in demo mode.",
        "trip": trip,
        "memory": memory
    })


@app.post("/api/reject")
def reject_booking():
    return jsonify({
        "success": True,
        "message": "Booking rejected. No action was taken."
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
