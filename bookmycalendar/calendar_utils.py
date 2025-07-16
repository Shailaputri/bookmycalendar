from datetime import datetime, timedelta
import pytz
import streamlit as st

# Get TIMEZONE from Streamlit secrets (fallback to default)
TIMEZONE = st.secrets.get("timezone", "Asia/Kolkata")

def get_available_slots(service, date):
    """Get available 30-minute slots between 10:00 and 17:00 for given date"""
    tz = pytz.timezone(TIMEZONE)
    start_date = datetime.combine(date, datetime.min.time())
    start_date = tz.localize(start_date) + timedelta(hours=10)  # 10:00 AM
    end_date = datetime.combine(date, datetime.min.time())
    end_date = tz.localize(end_date) + timedelta(hours=17)  # 5:00 PM
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_date.isoformat(),
        timeMax=end_date.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # Generate all possible 30-minute slots
    slots = []
    current_time = start_date
    while current_time + timedelta(minutes=30) <= end_date:
        slots.append(current_time)
        current_time += timedelta(minutes=30)
    
    # Filter out slots that overlap with existing events
    available_slots = []
    for slot in slots:
        slot_end = slot + timedelta(minutes=30)
        is_available = True
        
        for event in events:
            event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
            event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
            
            if not (slot_end <= event_start or slot >= event_end):
                is_available = False
                break
        
        if is_available:
            available_slots.append(slot)
    
    return available_slots

def create_appointment(service, start_time, name, email):
    """Create a calendar event for the appointment"""
    end_time = start_time + timedelta(minutes=30)
    tz = pytz.timezone(TIMEZONE)
    
    # Get admin email from secrets (fallback to default)
    admin_email = st.secrets.get("admin_email", "pooja@aipalette.com")
    
    event = {
        'summary': f'Appointment with {name}',
        'description': f'Appointment booked by {name} ({email})',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': TIMEZONE,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': TIMEZONE,
        },
        'attendees': [
            {'email': email},
            {'email': admin_email},
        ],
        'reminders': {
            'useDefault': True,
        },
    }
    
    return service.events().insert(
        calendarId='primary',
        body=event,
        sendUpdates="all"
    ).execute()