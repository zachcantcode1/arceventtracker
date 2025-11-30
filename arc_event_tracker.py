import requests
import json
import pytz
from datetime import datetime, timedelta, timezone

# Configuration
API_URL = "https://metaforge.app/api/arc-raiders/event-timers"
IFTTT_WEBHOOK_URL = "https://maker.ifttt.com/trigger/arc_map_events/with/key/pKdYziVhD9mH4gce0Odd-KYga4f6e9EOES1zlqFZjh1"

def get_events():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        return None

def filter_events_for_hour(data, target_hour_str):
    """
    Filters events that start at the target hour (format "HH:00").
    """
    upcoming_events = []
    if not data or 'data' not in data:
        return upcoming_events

    for item in data['data']:
        game = item.get('game')
        name = item.get('name')
        map_name = item.get('map')
        times = item.get('times', [])

        for time_slot in times:
            start_time = time_slot.get('start')
            if start_time == target_hour_str:
                upcoming_events.append({
                    "name": name,
                    "map": map_name,
                    "start": start_time,
                    "end": time_slot.get('end')
                })
    return upcoming_events

def format_message(events, display_time_str):
    if not events:
        return f"No map events starting at {display_time_str}."
    
    message = f"🗺️ ARC Raiders Map Events starting now! ({display_time_str})\n\n"
    for event in events:
        message += f"- {event['name']} on {event['map']}\n"
    
    return message

def send_webhook(message):
    payload = {"value1": message}
    try:
        response = requests.post(IFTTT_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Webhook sent successfully: {response.text}")
    except requests.RequestException as e:
        print(f"Error sending webhook: {e}")

def main():
    # Determine the target hour.
    # If running at the top of the hour (e.g., 10:00 - 10:29), target the current hour (10:00).
    # If running late in the hour (e.g., 10:30 - 10:59), target the next hour (11:00).
    
    now_utc = datetime.now(timezone.utc)
    
    if now_utc.minute < 30:
        # Target current hour
        target_time = now_utc.replace(minute=0, second=0, microsecond=0)
    else:
        # Target next hour
        target_time = (now_utc + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
    target_hour_str = target_time.strftime("%H:00")
    
    # Convert to Eastern Time for display
    eastern = pytz.timezone('US/Eastern')
    target_time_est = target_time.astimezone(eastern)
    display_time_str = target_time_est.strftime("%H:00 %Z")
    
    print(f"Checking events for: {target_hour_str} UTC ({display_time_str})")

    data = get_events()
    if data:
        events = filter_events_for_hour(data, target_hour_str)
        message = format_message(events, display_time_str)
        print("Generated Message:")
        print(message)
        
        if events:
            send_webhook(message)
        else:
            print("No events found, skipping webhook.")

if __name__ == "__main__":
    main()
