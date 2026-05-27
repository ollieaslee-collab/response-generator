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
    print(f"   Searching: intent={intent}, dur={duration_int}, dest={destinations}, festivals={festivals}")

    # 1. Archery – under adventure -> archery
    if is_archery and 'adventure' in ITINERARIES and 'archery' in ITINERARIES['adventure']:
        itin = get_itinerary_by_key(ITINERARIES['adventure'], 'archery', duration_int)
        if itin:
            return itin

    # 2. Shaman – under cultural -> shaman
    if is_shaman and 'cultural' in ITINERARIES and 'shaman' in ITINERARIES['cultural']:
        itin = get_itinerary_by_key(ITINERARIES['cultural'], 'shaman', duration_int)
        if itin:
            return itin

    # 3. Tsaatan (reindeer herders) – check both adventure->khuvsgul (winter) and cultural->reindeer_tribe_visit
    if is_tsaatan:
        # First try the winter reindeer expedition (adventure)
        if 'adventure' in ITINERARIES and 'khuvsgul' in ITINERARIES['adventure']:
            itin = get_itinerary_by_key(ITINERARIES['adventure'], 'khuvsgul', duration_int)
            if itin:
                return itin
        # Then try the cultural reindeer tribe visit
        if 'cultural' in ITINERARIES and 'reindeer_tribe_visit' in ITINERARIES['cultural']:
            itin = get_itinerary_by_key(ITINERARIES['cultural'], 'reindeer_tribe_visit', duration_int)
            if itin:
                return itin

    # 4. Festivals – map detection fest name to DB keys
    fest_map = {
        'ice': 'ice_reindeer_festival',
        'eagle': 'golden_eagle',
        'naadam': 'naadam_ub'   # default to UB naadam; you could add logic for Arvaikheer later
    }
    for fest in festivals:
        db_key = fest_map.get(fest)
        if db_key and 'festival' in ITINERARIES and db_key in ITINERARIES['festival']:
            itin = get_itinerary_by_key(ITINERARIES['festival'], db_key, duration_int)
            if itin:
                return itin

    # 5. Eagle hunter (non‑festival) – under cultural -> eagle_hunter_visit
    if is_eagle and not festivals:
        if 'cultural' in ITINERARIES and 'eagle_hunter_visit' in ITINERARIES['cultural']:
            itin = get_itinerary_by_key(ITINERARIES['cultural'], 'eagle_hunter_visit', duration_int)
            if itin:
                return itin

    # 6. Adventure by destination – map destinations to adventure keys
    adv_map = {
        'khuvsgul': 'khuvsgul',
        'terelj': 'terelj_short_trek',      # you can also handle dog sledding separately if winter keyword exists
        'altai': 'western_horse_riding',
        'olgii': 'western_horse_riding',
        'bulgan': 'bulgan',
        'mountain': 'mountain_lakes_reindeer'   # for "mountain lakes and reindeer"
    }
    if 'adventure' in intent.lower() or destinations:
        for dest in destinations:
            d = dest.lower()
            for kw, adv_key in adv_map.items():
                if kw in d and 'adventure' in ITINERARIES and adv_key in ITINERARIES['adventure']:
                    itin = get_itinerary_by_key(ITINERARIES['adventure'], adv_key, duration_int)
                    if itin:
                        return itin

    # 7. Cultural by destination – map destinations to cultural keys
    cult_map = {
        'gobi': 'gobi',
        'shaman': 'shaman',       # already handled above, but here for dest-based
        'photography': 'photography'
    }
    if 'cultural' in intent.lower():
        for dest in destinations:
            d = dest.lower()
            for kw, cult_key in cult_map.items():
                if kw in d and 'cultural' in ITINERARIES and cult_key in ITINERARIES['cultural']:
                    itin = get_itinerary_by_key(ITINERARIES['cultural'], cult_key, duration_int)
                    if itin:
                        return itin

    # 8. Classic tours – map destinations to classic keys
    classic_map = {
        'ulaanbaatar': 'ulaanbaatar_terelj',
        'terelj': 'ulaanbaatar_terelj',
        'kharkhorin': 'kharhorin_mini_gobi_hustai',
        'orkhon': 'kharhorin_mini_gobi_hustai',
        'hustai': 'kharhorin_mini_gobi_hustai',
        'mini gobi': 'kharhorin_mini_gobi_hustai'
    }
    # If intent is Classic or no specific intent, try classic
    if 'classic' in intent.lower() or not destinations:
        for dest in destinations:
            d = dest.lower()
            for kw, classic_key in classic_map.items():
                if kw in d and 'classic' in ITINERARIES and classic_key in ITINERARIES['classic']:
                    itin = get_itinerary_by_key(ITINERARIES['classic'], classic_key, duration_int)
                    if itin:
                        return itin
        # Fallback: first classic tour
        if 'classic' in ITINERARIES:
            first_key = next(iter(ITINERARIES['classic']))
            itin = get_itinerary_by_key(ITINERARIES['classic'], first_key, duration_int)
            if itin:
                return itin

    # 9. Ultimate custom fallback
    return {
        "title": f"Custom {duration_int}-Day Mongolia Tour",
        "days": [f"Customized activities based on your interests." for _ in range(duration_int)]
    }

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
