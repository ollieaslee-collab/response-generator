# app.py
import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from your WordPress domain

# ---------- Load database (same as original) ----------
JSON_DB_FILE = "database.json"   # Must be in the same directory on Railway
with open(JSON_DB_FILE, 'r', encoding='utf-8') as f:
    db = json.load(f)

COMPANY_NAME = db['company']['name']
WEBSITE = db['company']['website']
EMAIL = db['company']['email']
PHONE = db['company']['phone']
COMPANY_DESC = db['company']['description']
TESTIMONIALS = db.get('testimonials', [])
CULTURAL_NOTES = db.get('cultural_notes', {})
FLIGHT_SCHEDULE = db['flight_schedule']
ITINERARIES = db['itineraries']
INCLUSIONS = db.get('inclusions', {})
EXCLUSIONS = db.get('exclusions', [])

print("✅ Database loaded", flush=True)

# ---------- Helper functions (copied from your script) ----------
def detect_shaman_from_text(text):
    text = text.lower()
    keywords = ['shaman', 'shamanism', 'shamanic', 'böö', 'boo ceremony', 'spiritual ceremony']
    return any(kw in text for kw in keywords)

def detect_archery_from_text(text):
    return 'archery' in text.lower()

def detect_tsaatan_from_text(text):
    text = text.lower()
    return any(kw in text for kw in ['tsaatan', 'reindeer', 'dukha', 'reindeer herders'])

def detect_eagle_from_text(text):
    text = text.lower()
    return any(kw in text for kw in ['eagle', 'eagle hunter', 'eagle hunting', 'golden eagle'])

def detect_festivals_from_text(text):
    text = text.lower()
    festivals = []
    if 'ice festival' in text:
        festivals.append('ice')
    if 'golden eagle festival' in text or 'eagle festival' in text:
        festivals.append('eagle')
    if 'naadam' in text:
        festivals.append('naadam')
    return festivals

def extract_destinations(dest_str, email_text):
    destinations = []
    if dest_str and dest_str.lower() != 'not specified':
        if ',' in dest_str:
            destinations = [d.strip() for d in dest_str.split(',')]
        else:
            destinations = [dest_str.strip()]
    text = email_text.lower()
    if 'khuvsgul' in text and 'Lake Khuvsgul' not in destinations:
        destinations.append('Lake Khuvsgul')
    if 'terelj' in text and 'Terelj National Park' not in destinations:
        destinations.append('Terelj National Park')
    if 'gobi' in text and 'Gobi Desert' not in destinations:
        destinations.append('Gobi Desert')
    if 'ulaanbaatar' in text and 'Ulaanbaatar' not in destinations:
        destinations.append('Ulaanbaatar')
    return destinations

def get_duration(duration_str):
    if duration_str:
        nums = re.findall(r'\d+', str(duration_str))
        if nums:
            return nums[0]
    return "7"

def extract_timing(timing_str):
    if timing_str:
        return str(timing_str)
    return "your preferred dates"

def extract_group_size(group_str):
    return str(group_str) if group_str else ""

def get_complexity(complexity_str):
    return str(complexity_str) if complexity_str else "Low"

def find_closest_duration(available, target):
    if not available:
        return None
    return min(available, key=lambda x: abs(x - target))

def get_itinerary_by_key(data, key, target_duration):
    if key not in data:
        return None
    available = [int(k) for k in data[key].keys() if k.isdigit()]
    if not available:
        return None
    closest = find_closest_duration(available, target_duration)
    if closest is not None:
        return data[key][str(closest)]
    return None

def find_itinerary(intent, destinations, duration, is_shaman, is_archery, is_tsaatan, festivals, is_eagle):
    duration_int = int(duration) if duration and duration.isdigit() else 7

    # 1. Archery
    if is_archery and 'adventure' in ITINERARIES and 'archery' in ITINERARIES['adventure']:
        itin = get_itinerary_by_key(ITINERARIES['adventure'], 'archery', duration_int)
        if itin:
            return itin

    # 2. Shaman
    if is_shaman:
        if 'shaman' in ITINERARIES:
            itin = get_itinerary_by_key(ITINERARIES, 'shaman', duration_int)
            if itin:
                return itin
        if 'cultural' in ITINERARIES and 'shaman_khuvsgul' in ITINERARIES['cultural']:
            itin = get_itinerary_by_key(ITINERARIES['cultural'], 'shaman_khuvsgul', duration_int)
            if itin:
                return itin

    # 3. Tsaatan
    if is_tsaatan and 'adventure' in ITINERARIES and 'khuvsgul' in ITINERARIES['adventure']:
        itin = get_itinerary_by_key(ITINERARIES['adventure'], 'khuvsgul', duration_int)
        if itin:
            return itin

    # 4. Festivals
    for fest in festivals:
        if fest in ('ice', 'eagle', 'naadam') and 'festival' in ITINERARIES and fest in ITINERARIES['festival']:
            itin = get_itinerary_by_key(ITINERARIES['festival'], fest, duration_int)
            if itin:
                return itin

    # 5. Eagle Hunter (non-festival)
    if is_eagle and not festivals:
        if 'eagle_hunter' in ITINERARIES:
            itin = get_itinerary_by_key(ITINERARIES, 'eagle_hunter', duration_int)
            if itin:
                return itin

    # 6. Adventure by destination
    if 'adventure' in intent.lower() or ('classic' in intent.lower() and destinations):
        for dest in destinations:
            d = dest.lower()
            if 'gobi' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'gobi', duration_int)
                if itin:
                    return itin
            elif 'khuvsgul' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'khuvsgul', duration_int)
                if itin:
                    return itin
            elif 'terelj' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'terelj', duration_int)
                if itin:
                    return itin
            elif 'altai' in d or 'olgii' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'olgii', duration_int)
                if itin:
                    return itin

    # 7. Cultural by destination
    if 'cultural' in intent.lower() or ('classic' in intent.lower() and destinations):
        for dest in destinations:
            d = dest.lower()
            if 'ulaanbaatar' in d:
                itin = get_itinerary_by_key(ITINERARIES['cultural'], 'ulaanbaatar', duration_int)
                if itin:
                    return itin
            elif 'kharkhorin' in d or 'orkhon' in d:
                itin = get_itinerary_by_key(ITINERARIES['cultural'], 'kharkhorin', duration_int)
                if itin:
                    return itin

    # 8. Default Cultural
    if 'cultural' in intent.lower():
        itin = get_itinerary_by_key(ITINERARIES['cultural'], 'ulaanbaatar', duration_int)
        if itin:
            return itin

    # 9. Default Adventure
    if 'adventure' in intent.lower():
        itin = get_itinerary_by_key(ITINERARIES['adventure'], 'terelj', duration_int)
        if itin:
            return itin

    # 10. Classic highlights
    if 'classic' in ITINERARIES and 'highlights' in ITINERARIES['classic']:
        itin = get_itinerary_by_key(ITINERARIES['classic'], 'highlights', duration_int)
        if itin:
            return itin

    # 11. Fallback
    return {
        "title": f"Custom {duration_int}-Day Mongolia Tour",
        "days": [f"Customized activities based on your interests." for _ in range(duration_int)]
    }

def get_flight_text(flights):
    if not flights:
        return ""
    text = "\n✈️ **FLIGHT INFORMATION**\n" + "-" * 40 + "\n"
    for f in flights:
        if f in FLIGHT_SCHEDULE:
            fl = FLIGHT_SCHEDULE[f]
            days = ', '.join(fl['departure_days'])
            text += f"**{fl['region']}:** Flights on {days} at {fl['departure_time']} ({fl['flight_duration']})\n"
    text += "\nWe will coordinate your dates with these schedules.\n"
    return text

def generate_response(inquiry_dict):
    """
    Generate response from a dictionary containing:
      - Email Request (string)
      - Intent (string)
      - Destination (string)
      - Duration (string)
      - Tour Timing (string)
      - Group Size (string)
      - Complexity (string)
    """
    email_text = inquiry_dict.get('Email Request', '')
    intent = inquiry_dict.get('Intent', 'Classic')
    duration = get_duration(inquiry_dict.get('Duration', ''))
    dest_str = inquiry_dict.get('Destination', '')
    destinations = extract_destinations(dest_str, email_text)
    timing = extract_timing(inquiry_dict.get('Tour Timing', ''))
    group_size = extract_group_size(inquiry_dict.get('Group Size', ''))
    complexity = get_complexity(inquiry_dict.get('Complexity', ''))

    is_shaman = detect_shaman_from_text(email_text)
    is_archery = detect_archery_from_text(email_text)
    is_tsaatan = detect_tsaatan_from_text(email_text)
    festivals = detect_festivals_from_text(email_text)
    is_eagle = detect_eagle_from_text(email_text)

    # Determine flights
    flights = set()
    for dest in destinations:
        d = dest.lower()
        if 'gobi' in d:
            flights.add('gobi')
        if 'khuvsgul' in d or 'murun' in d:
            flights.add('khuvsgul')
        if 'olgii' in d or 'altai' in d:
            flights.add('olgii')
    if is_tsaatan or any('khuvsgul' in d for d in destinations):
        flights.add('khuvsgul')
    if is_eagle or 'eagle' in festivals:
        flights.add('olgii')

    flight_text = get_flight_text(list(flights))
    requires_flight = len(flights) > 0

    # Get itinerary
    itin_data = find_itinerary(intent, destinations, duration, is_shaman, is_archery, is_tsaatan, festivals, is_eagle)
    title = itin_data.get('title', f'{intent} Tour')
    days = itin_data.get('days', [])
    itinerary_text = f"**{title}**\n\n"
    for i, day in enumerate(days, 1):
        clean_day = re.sub(r'^Day\s*\d+:\s*', '', day)
        itinerary_text += f"**Day {i}:** {clean_day}\n"

    # Cultural notes
    notes = []
    if is_shaman:
        notes.append(CULTURAL_NOTES.get('shaman', ''))
    if is_archery:
        notes.append(CULTURAL_NOTES.get('horse_archery', ''))
    if is_tsaatan:
        notes.append(CULTURAL_NOTES.get('khuvsgul', ''))
    for fest in festivals:
        if fest == 'ice':
            notes.append(CULTURAL_NOTES.get('ice_festival', ''))
        elif fest == 'eagle':
            notes.append(CULTURAL_NOTES.get('eagle', ''))
        elif fest == 'naadam':
            notes.append(CULTURAL_NOTES.get('naadam', ''))
    if is_eagle and not festivals:
        notes.append(CULTURAL_NOTES.get('eagle_hunter', ''))
    for dest in destinations:
        d = dest.lower()
        if 'khuvsgul' in d and not is_tsaatan:
            notes.append(CULTURAL_NOTES.get('khuvsgul', ''))
        if 'gobi' in d:
            notes.append(CULTURAL_NOTES.get('gobi', ''))
        if 'terelj' in d:
            notes.append(CULTURAL_NOTES.get('terelj', ''))
        if 'altai' in d or 'olgii' in d:
            notes.append(CULTURAL_NOTES.get('altai', ''))
    cultural_notes = [n for n in notes if n][:3]

    # Testimonial
    testimonial = TESTIMONIALS[0] if TESTIMONIALS else None
    for test in TESTIMONIALS:
        if is_shaman and 'shaman' in test.get('destinations', []):
            testimonial = test
            break
        if is_archery and 'archery' in test.get('destinations', []):
            testimonial = test
            break

    # Build email
    response = f"Dear Valued Customer,\n\nThank you for your interest in traveling to Mongolia with {COMPANY_NAME}. {COMPANY_DESC}\n"
    response += "\n📋 **From your inquiry, we've concluded the below**\n" + "-" * 40 + "\n"
    response += f"✓ Travel Style: {intent}\n"
    if destinations:
        response += f"✓ Destinations: {', '.join(destinations)}\n"
    if timing and timing != "your preferred dates":
        response += f"✓ Travel Period: {timing}\n"
    response += f"✓ Duration: {duration} days\n"
    if group_size:
        response += f"✓ Group Size: {group_size} traveler(s)\n"
    response += f"✓ Complexity Level: {complexity}\n"

    response += "\n🏔️ **RECOMMENDED ITINERARY FOR YOU**\n" + "-" * 40 + "\n"
    response += itinerary_text

    if cultural_notes:
        response += "\n📖 **CULTURAL INSIGHTS**\n" + "-" * 40 + "\n"
        for note in cultural_notes:
            response += f"• {note}\n"

    if flight_text:
        response += flight_text

    if testimonial:
        response += "\n⭐ **WHAT OUR TRAVELERS SAY**\n" + "-" * 40 + "\n"
        response += f"\"{testimonial['text'][:300]}...\"\n"
        response += f"— {testimonial['name']}, {testimonial['location']}\n"

    response += "\n✅ **WHAT'S INCLUDED**\n" + "-" * 40 + "\n"
    for item in INCLUSIONS.get('standard', []):
        response += f"✓ {item}\n"
    if requires_flight:
        for item in INCLUSIONS.get('flight', []):
            response += f"✓ {item}\n"

    response += "\n❌ **WHAT'S NOT INCLUDED**\n" + "-" * 40 + "\n"
    for item in EXCLUSIONS:
        response += f"✗ {item}\n"

    response += "\n📞 **NEXT STEPS FOR YOU**\n" + "-" * 40 + "\n"
    response += "1. Review the recommended itinerary above\n"
    response += "2. Let us know if you would like any modifications\n"
    response += "3. Confirm your preferred travel dates\n\n"
    response += "➡️ **Once you confirm no modifications, we will prepare and send the detailed price quote.**\n"
    response += "\nWe are happy to customize this itinerary to match your exact preferences.\n"
    response += f"\n\nThank you for considering {COMPANY_NAME}. We look forward to welcoming you to the Land of the Blue Sky!\n\nBest regards,\n\nTravel Specialist\n{COMPANY_NAME}\n{PHONE}\n{EMAIL}\n{WEBSITE}"
    return response

# ---------- API Endpoint ----------
API_KEY = os.environ.get('API_KEY', 'change-this-in-railway')

@app.route('/generate', methods=['POST'])
def generate():
    # Authenticate
    provided_key = request.headers.get('X-API-Key')
    if provided_key != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate required field
    if 'Email Request' not in data:
        return jsonify({'error': 'Missing field: Email Request'}), 400

    # Set defaults for optional fields
    defaults = {
        'Intent': 'Classic',
        'Group Size': '',
        'Destination': 'Not Specified',
        'Duration': '7',
        'Complexity': 'Low',
        'Tour Timing': 'your preferred dates'
    }
    for key, val in defaults.items():
        if key not in data:
            data[key] = val

    try:
        response_text = generate_response(data)
        return jsonify({'response': response_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)