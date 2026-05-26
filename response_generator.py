import json
import re
from datetime import datetime

# Load database once
with open('database.json', 'r', encoding='utf-8') as f:
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

# ------------------------------------------------------------------
# Helper functions (copy from your working script, adapted slightly)
# ------------------------------------------------------------------

def extract_destinations_from_text(text):
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    found = []
    # Simple keyword matching (extend as needed)
    if 'tsaatan' in text_lower or 'reindeer' in text_lower:
        found.append('Tsaatan Reindeer Tribe')
    if 'gobi' in text_lower:
        found.append('Gobi Desert')
    if 'khuvsgul' in text_lower or 'murun' in text_lower:
        found.append('Lake Khuvsgul')
    if 'altai' in text_lower or 'olgii' in text_lower:
        found.append('Altai Mountains')
    if 'terelj' in text_lower:
        found.append('Terelj National Park')
    if 'ulaanbaatar' in text_lower or 'ub' in text_lower:
        found.append('Ulaanbaatar')
    return list(set(found))

def extract_timing_from_text(text):
    months = ['january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december']
    text_lower = text.lower()
    for month in months:
        if month in text_lower:
            return month.capitalize()
    return "your preferred dates"

def extract_group_size_from_text(text):
    match = re.search(r'(\d+)\s*(people|pax|group|adults|travelers)', text.lower())
    return match.group(1) if match else ""

def extract_duration_from_text(text):
    match = re.search(r'(\d+)\s*days?', text.lower())
    return match.group(1) if match else "7"

def detect_shaman_from_text(text):
    keywords = ['shaman', 'shamanism', 'shamanic', 'böö', 'boo ceremony', 'spiritual ceremony']
    return any(kw in text.lower() for kw in keywords)

def detect_archery_from_text(text):
    return 'archery' in text.lower()

def detect_tsaatan_from_text(text):
    keywords = ['tsaatan', 'reindeer', 'dukha', 'reindeer herders']
    return any(kw in text.lower() for kw in keywords)

def detect_festivals_from_text(text):
    text_lower = text.lower()
    festivals = []
    if 'ice festival' in text_lower:
        festivals.append('ice')
    if 'golden eagle festival' in text_lower or 'eagle festival' in text_lower:
        festivals.append('eagle')
    if 'naadam' in text_lower:
        festivals.append('naadam')
    return festivals

def detect_eagle_from_text(text):
    keywords = ['eagle', 'eagle hunter', 'eagle hunting', 'golden eagle']
    return any(kw in text.lower() for kw in keywords)

def find_closest_duration(available, target):
    if not available:
        return None
    return min(available, key=lambda x: abs(x - target))

def get_itinerary_by_key(data_dict, key, target_duration):
    if key not in data_dict:
        return None
    available = [int(k) for k in data_dict[key].keys() if k.isdigit()]
    if not available:
        return None
    closest = find_closest_duration(available, target_duration)
    return data_dict[key][str(closest)]

def find_itinerary(intent, destinations, duration, is_shaman, is_archery, is_tsaatan, festivals, is_eagle):
    duration_int = int(duration) if duration.isdigit() else 7
    print(f"   Searching: intent={intent}, dur={duration_int}, dest={destinations}")

    # 1. Archery
    if is_archery and 'adventure' in ITINERARIES and 'archery' in ITINERARIES['adventure']:
        itin = get_itinerary_by_key(ITINERARIES['adventure'], 'archery', duration_int)
        if itin:
            return itin, 'archery'

    # 2. Shaman (general section first)
    if is_shaman:
        if 'shaman' in ITINERARIES:
            itin = get_itinerary_by_key(ITINERARIES, 'shaman', duration_int)
            if itin:
                return itin, 'shaman_general'
        if 'cultural' in ITINERARIES and 'shaman_khuvsgul' in ITINERARIES['cultural']:
            itin = get_itinerary_by_key(ITINERARIES['cultural'], 'shaman_khuvsgul', duration_int)
            if itin:
                return itin, 'shaman_khuvsgul'

    # 3. Tsaatan
    if is_tsaatan and 'adventure' in ITINERARIES and 'khuvsgul' in ITINERARIES['adventure']:
        itin = get_itinerary_by_key(ITINERARIES['adventure'], 'khuvsgul', duration_int)
        if itin:
            return itin, 'tsaatan'

    # 4. Festivals
    for fest in festivals:
        if fest in ('ice', 'eagle', 'naadam') and 'festival' in ITINERARIES and fest in ITINERARIES['festival']:
            itin = get_itinerary_by_key(ITINERARIES['festival'], fest, duration_int)
            if itin:
                return itin, f'{fest}_festival'

    # 5. Eagle hunter
    if is_eagle and 'eagle_hunter' in ITINERARIES:
        itin = get_itinerary_by_key(ITINERARIES, 'eagle_hunter', duration_int)
        if itin:
            return itin, 'eagle_hunter'

    # 6. Adventure by destination
    if 'adventure' in intent.lower() or destinations:
        for dest in destinations:
            d = dest.lower()
            if 'gobi' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'gobi', duration_int)
                if itin:
                    return itin, 'adventure_gobi'
            if 'khuvsgul' in d or 'murun' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'khuvsgul', duration_int)
                if itin:
                    return itin, 'adventure_khuvsgul'
            if 'terelj' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'terelj', duration_int)
                if itin:
                    return itin, 'adventure_terelj'
            if 'altai' in d or 'olgii' in d:
                itin = get_itinerary_by_key(ITINERARIES['adventure'], 'olgii', duration_int)
                if itin:
                    return itin, 'adventure_olgii'

    # 7. Cultural by destination
    if 'cultural' in intent.lower():
        for dest in destinations:
            d = dest.lower()
            if 'ulaanbaatar' in d:
                itin = get_itinerary_by_key(ITINERARIES['cultural'], 'ulaanbaatar', duration_int)
                if itin:
                    return itin, 'cultural_ub'
            if 'kharkhorin' in d or 'orkhon' in d:
                itin = get_itinerary_by_key(ITINERARIES['cultural'], 'kharkhorin', duration_int)
                if itin:
                    return itin, 'cultural_kharkhorin'

    # 8. Classic highlights (fallback)
    if 'classic' in ITINERARIES and 'highlights' in ITINERARIES['classic']:
        itin = get_itinerary_by_key(ITINERARIES['classic'], 'highlights', duration_int)
        if itin:
            return itin, 'classic'

    # 9. Custom fallback
    return {
        "title": f"Custom {duration_int}-Day Mongolia Tour",
        "days": [f"Customized activities based on your interests." for _ in range(duration_int)]
    }, 'custom'

def build_email_response(inquiry_text, override_intent=None, override_duration=None, override_destinations=None):
    # Extract from text if not overridden
    intent = override_intent if override_intent else 'Classic'
    duration = override_duration if override_duration else extract_duration_from_text(inquiry_text)
    destinations = override_destinations if override_destinations else extract_destinations_from_text(inquiry_text)
    timing = extract_timing_from_text(inquiry_text)
    group_size = extract_group_size_from_text(inquiry_text)

    # Run detections
    is_shaman = detect_shaman_from_text(inquiry_text)
    is_archery = detect_archery_from_text(inquiry_text)
    is_tsaatan = detect_tsaatan_from_text(inquiry_text)
    festivals = detect_festivals_from_text(inquiry_text)
    is_eagle = detect_eagle_from_text(inquiry_text)

    # Find itinerary
    itinerary_data, match_type = find_itinerary(intent, destinations, duration, is_shaman, is_archery, is_tsaatan, festivals, is_eagle)
    title = itinerary_data.get('title', f'{intent} Tour')
    days = itinerary_data.get('days', [])

    # Format itinerary text
    itinerary_text = f"**{title}**\n\n"
    for i, day in enumerate(days, 1):
        clean_day = re.sub(r'^Day\s*\d+:\s*', '', day)
        itinerary_text += f"**Day {i}:** {clean_day}\n"

    # Flight detection
    flights = set()
    for dest in destinations:
        d = dest.lower()
        if 'gobi' in d:
            flights.add('gobi')
        if 'khuvsgul' in d or 'murun' in d:
            flights.add('khuvsgul')
        if 'olgii' in d or 'altai' in d:
            flights.add('olgii')
    if is_tsaatan:
        flights.add('khuvsgul')
    if is_eagle or 'eagle' in festivals:
        flights.add('olgii')
    flight_text = ""
    if flights:
        flight_text = "\n✈️ **FLIGHT INFORMATION**\n" + "-" * 40 + "\n"
        for f in flights:
            if f in FLIGHT_SCHEDULE:
                fl = FLIGHT_SCHEDULE[f]
                days_str = ', '.join(fl['departure_days'])
                flight_text += f"**{fl['region']}:** Flights on {days_str} at {fl['departure_time']} ({fl['flight_duration']})\n"
        flight_text += "\nWe will coordinate your dates with these schedules.\n"

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
    notes = [n for n in notes if n][:3]
    cultural_text = ""
    if notes:
        cultural_text = "\n📖 **CULTURAL INSIGHTS**\n" + "-" * 40 + "\n" + "\n".join(f"• {n}" for n in notes) + "\n"

    # Testimonial (simple fallback)
    testimonial = TESTIMONIALS[0] if TESTIMONIALS else None
    for t in TESTIMONIALS:
        if is_shaman and 'shaman' in t.get('destinations', []):
            testimonial = t
            break
        if is_archery and 'archery' in t.get('destinations', []):
            testimonial = t
            break
    testimonial_text = ""
    if testimonial:
        testimonial_text = f"\n⭐ **WHAT OUR TRAVELERS SAY**\n" + "-" * 40 + "\n" + f"\"{testimonial['text'][:300]}...\"\n— {testimonial['name']}, {testimonial['location']}\n"

    # Assemble final email
    email = f"Dear Valued Customer,\n\nThank you for your interest in traveling to Mongolia with {COMPANY_NAME}. {COMPANY_DESC}\n"
    email += "\n📋 **From your inquiry, we've concluded the below**\n" + "-" * 40 + "\n"
    email += f"✓ Travel Style: {intent}\n"
    if destinations:
        email += f"✓ Destinations: {', '.join(destinations)}\n"
    if timing and timing != "your preferred dates":
        email += f"✓ Travel Period: {timing}\n"
    email += f"✓ Duration: {duration} days\n"
    if group_size:
        email += f"✓ Group Size: {group_size} traveler(s)\n"
    email += "\n🏔️ **RECOMMENDED ITINERARY FOR YOU**\n" + "-" * 40 + "\n"
    email += itinerary_text
    email += cultural_text
    if flight_text:
        email += flight_text
    if testimonial_text:
        email += testimonial_text
    email += "\n✅ **WHAT'S INCLUDED**\n" + "-" * 40 + "\n"
    for item in INCLUSIONS.get('standard', []):
        email += f"✓ {item}\n"
    if flights:
        for item in INCLUSIONS.get('flight', []):
            email += f"✓ {item}\n"
    email += "\n❌ **WHAT'S NOT INCLUDED**\n" + "-" * 40 + "\n"
    for item in EXCLUSIONS:
        email += f"✗ {item}\n"
    email += "\n📞 **NEXT STEPS FOR YOU**\n" + "-" * 40 + "\n"
    email += "1. Review the recommended itinerary above\n"
    email += "2. Let us know if you would like any modifications\n"
    email += "3. Confirm your preferred travel dates\n\n"
    email += "➡️ **Once you confirm no modifications, we will prepare and send the detailed price quote.**\n"
    email += "\nWe are happy to customize this itinerary to match your exact preferences.\n"
    email += f"\n\nThank you for considering {COMPANY_NAME}. We look forward to welcoming you to the Land of the Blue Sky!\n\nBest regards,\n\nTravel Specialist\n{COMPANY_NAME}\n{PHONE}\n{EMAIL}\n{WEBSITE}"

    # Metadata for web display
    metadata = {
        'intent': intent,
        'duration': duration,
        'destinations': destinations,
        'timing': timing,
        'group_size': group_size,
        'itinerary_title': title,
        'match_type': match_type,
        'requires_flight': len(flights) > 0,
        'flights': list(flights),
        'special_activities': [],
        'confidence': 0.85  # placeholder
    }
    if is_shaman:
        metadata['special_activities'].append('shaman')
    if is_archery:
        metadata['special_activities'].append('horse archery')
    if is_tsaatan:
        metadata['special_activities'].append('tsaatan')
    if festivals:
        metadata['special_activities'].extend(festivals)

    return email, metadata
