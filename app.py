"""
BRACU Free Room Finder — Flask Backend
Serves the API and the frontend index.html
"""

from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import json
import os

app = Flask(__name__, static_folder="static")

# ── Load schedule data once at startup ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "schedule.json"), "r") as f:
    SCHEDULE = json.load(f)

# Pre-compute the full set of rooms
ALL_ROOMS = sorted(set(entry["room"] for entry in SCHEDULE))


# ── Helpers ─────────────────────────────────────────────────────────────────

def to_minutes(time_str: str) -> int:
    """Convert '02:00 PM' → total minutes since midnight."""
    t = datetime.strptime(time_str.strip(), "%I:%M %p")
    return t.hour * 60 + t.minute


def busy_rooms_at(day: str, query_start: int, query_end: int) -> set:
    """Return set of room codes that have a class overlapping the given window."""
    busy = set()
    day_upper = day.upper()
    for entry in SCHEDULE:
        if entry["day"] != day_upper:
            continue
        class_start = to_minutes(entry["start_time"])
        class_end   = to_minutes(entry["end_time"])
        # Overlap: class starts before query ends AND class ends after query starts
        if class_start < query_end and class_end > query_start:
            busy.add(entry["room"])
    return busy


def classes_in_room(day: str, room: str) -> list:
    """Return all classes scheduled in a room on a day (sorted by start time)."""
    day_upper = day.upper()
    result = []
    for entry in SCHEDULE:
        if entry["day"] == day_upper and entry["room"] == room:
            result.append(entry)
    result.sort(key=lambda e: to_minutes(e["start_time"]))
    return result


# ── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/free-rooms")
def free_rooms():
    """
    GET /api/free-rooms?day=MONDAY&start=02:00 PM&end=03:20 PM

    Returns JSON with free rooms and busy rooms for the given window.
    """
    day        = request.args.get("day", "").strip().upper()
    start_str  = request.args.get("start", "").strip()
    end_str    = request.args.get("end", "").strip()

    valid_days = {"SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"}
    if day not in valid_days:
        return jsonify({"error": "Invalid day. Use SUNDAY–SATURDAY."}), 400

    try:
        query_start = to_minutes(start_str)
        query_end   = to_minutes(end_str)
    except ValueError:
        return jsonify({"error": "Invalid time format. Use HH:MM AM/PM (e.g. 02:00 PM)."}), 400

    if query_start >= query_end:
        return jsonify({"error": "Start time must be before end time."}), 400

    busy   = busy_rooms_at(day, query_start, query_end)
    free   = sorted(r for r in ALL_ROOMS if r not in busy)

    # Enrich free rooms with their next class on that day
    enriched_free = []
    for room in free:
        todays_classes = classes_in_room(day, room)
        next_class = None
        for cls in todays_classes:
            if to_minutes(cls["start_time"]) >= query_end:
                next_class = {
                    "course":     cls["course"],
                    "start_time": cls["start_time"],
                    "end_time":   cls["end_time"],
                }
                break
        enriched_free.append({
            "room":       room,
            "next_class": next_class,
        })

    return jsonify({
        "day":        day,
        "start":      start_str,
        "end":        end_str,
        "total_rooms": len(ALL_ROOMS),
        "free_count": len(free),
        "busy_count": len(busy),
        "free_rooms": enriched_free,
    })


@app.route("/api/room-schedule")
def room_schedule():
    """
    GET /api/room-schedule?day=MONDAY&room=07A-01C

    Returns all classes in a given room on a given day.
    """
    day  = request.args.get("day", "").strip().upper()
    room = request.args.get("room", "").strip().upper()

    classes = classes_in_room(day, room)
    return jsonify({"day": day, "room": room, "classes": classes})


@app.route("/api/all-rooms")
def all_rooms():
    """GET /api/all-rooms — Return every unique room code."""
    return jsonify({"rooms": ALL_ROOMS, "count": len(ALL_ROOMS)})


@app.route("/api/stats")
def stats():
    """GET /api/stats — Basic data stats."""
    days = {}
    for e in SCHEDULE:
        days[e["day"]] = days.get(e["day"], 0) + 1
    return jsonify({
        "total_entries": len(SCHEDULE),
        "total_rooms":   len(ALL_ROOMS),
        "entries_per_day": days,
    })


# ── Serve Frontend ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
