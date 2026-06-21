"""
parse_schedule.py
─────────────────
Standalone script to parse the BRACU class schedule PDF
and produce schedule.json.

Usage:
    python parse_schedule.py                         # uses default path
    python parse_schedule.py path/to/schedule.pdf    # custom path
"""

import json
import re
import sys
import os
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("pdfplumber not found. Run:  pip install pdfplumber")
    sys.exit(1)


# ── Config ───────────────────────────────────────────────────────────────────

DEFAULT_PDF = "Class_Schedule_Summer_2026.pdf"
OUTPUT_JSON = "schedule.json"

VALID_DAYS = {
    "SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY",
    "THURSDAY", "FRIDAY", "SATURDAY"
}

DAY_ABBR = {
    "SUNDAY": "SUN", "MONDAY": "MON", "TUESDAY": "TUE",
    "WEDNESDAY": "WED", "THURSDAY": "THU", "FRIDAY": "FRI", "SATURDAY": "SAT"
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_24h(time_str: str) -> str:
    """Convert '02:00 PM' → '14:00' for sorting; return original on fail."""
    try:
        t = datetime.strptime(time_str.strip(), "%I:%M %p")
        return t.strftime("%H:%M")
    except ValueError:
        return time_str


def extract_room(room_raw: str, day: str, start_time: str) -> str:
    """
    Handle both simple rooms ('07A-01C') and compound room strings
    like 'SUN 2:00PM: 07A-08C; TUE 3:30PM: 09G-31T'.
    """
    room_raw = room_raw.strip()

    # Simple case — no day prefix
    if not re.search(r'\b(SUN|MON|TUE|WED|THU|FRI|SAT)\b', room_raw):
        return room_raw

    day_abbr = DAY_ABBR.get(day.upper(), "")

    # Convert start_time to the compact key used in the room string (e.g. "2:00PM")
    try:
        t = datetime.strptime(start_time.strip(), "%I:%M %p")
        time_key = t.strftime("%-I:%M%p").upper()        # Linux / Mac
    except ValueError:
        time_key = ""

    # Primary match: "SUN 2:00PM: 07A-08C"
    pattern = rf'\b{day_abbr}\s+{re.escape(time_key)}:\s*([\w\-]+)'
    m = re.search(pattern, room_raw, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Secondary match: first room code after this day's prefix
    segments = room_raw.split(";")
    for seg in segments:
        seg = seg.strip()
        if seg.upper().startswith(day_abbr):
            room_m = re.search(r':\s*([\w\-]+)\s*$', seg)
            if room_m:
                return room_m.group(1).strip()

    # Fallback: grab any room-shaped token (digits + letter dash digits + letter)
    rooms = re.findall(r'\b(\d+[A-Z]-\d+[A-Z])\b', room_raw)
    if rooms:
        return rooms[0]

    return room_raw   # give up, return raw


# ── Line Patterns ────────────────────────────────────────────────────────────

# With faculty code:  SL COURSE FACULTY SECTION DAY HH:MM AM HH:MM AM room…
PAT_WITH_FACULTY = re.compile(
    r'^(\d+)\s+'                         # SL
    r'(\S+)\s+'                           # Course
    r'(\S+)\s+'                           # Faculty
    r'(\S+)\s+'                           # Section
    r'(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)\s+'
    r'(\d{2}:\d{2}\s+[AP]M)\s+'
    r'(\d{2}:\d{2}\s+[AP]M)\s+'
    r'(.+)$'
)

# Without faculty:    SL COURSE SECTION DAY …
PAT_NO_FACULTY = re.compile(
    r'^(\d+)\s+'
    r'(\S+)\s+'
    r'(\S+)\s+'
    r'(SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY)\s+'
    r'(\d{2}:\d{2}\s+[AP]M)\s+'
    r'(\d{2}:\d{2}\s+[AP]M)\s+'
    r'(.+)$'
)


# ── Main Parser ──────────────────────────────────────────────────────────────

def parse_pdf(pdf_path: str) -> list:
    entries = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Skip headers
                if "SL" in line and "Course" in line:
                    continue
                if "BRAC University" in line or "Class Schedule" in line:
                    continue

                # Try with-faculty pattern first
                m = PAT_WITH_FACULTY.match(line)
                if m:
                    sl, course, faculty, section, day, start, end, room_raw = m.groups()
                    room = extract_room(room_raw, day, start)
                    entries.append({
                        "sl":         int(sl),
                        "course":     course,
                        "faculty":    faculty,
                        "section":    section,
                        "day":        day,
                        "start_time": start.strip(),
                        "end_time":   end.strip(),
                        "room":       room,
                    })
                    continue

                # Try no-faculty pattern
                m2 = PAT_NO_FACULTY.match(line)
                if m2:
                    sl, course, section, day, start, end, room_raw = m2.groups()
                    room = extract_room(room_raw, day, start)
                    entries.append({
                        "sl":         int(sl),
                        "course":     course,
                        "faculty":    "",
                        "section":    section,
                        "day":        day,
                        "start_time": start.strip(),
                        "end_time":   end.strip(),
                        "room":       room,
                    })

    return entries


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at '{pdf_path}'")
        sys.exit(1)

    print(f"Parsing {pdf_path} …")
    entries = parse_pdf(pdf_path)

    unique_rooms = sorted(set(e["room"] for e in entries))
    unique_days  = sorted(set(e["day"]  for e in entries))

    print(f"  ✓ {len(entries):,} schedule entries extracted")
    print(f"  ✓ {len(unique_rooms)} unique rooms")
    print(f"  ✓ Days covered: {', '.join(unique_days)}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\nSaved → {OUTPUT_JSON}")
