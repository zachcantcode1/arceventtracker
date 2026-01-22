import requests
import json
import pytz
import base64
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
API_URL = "https://metaforge.app/api/arc-raiders/events-schedule"
IFTTT_WEBHOOK_URL = "https://maker.ifttt.com/trigger/arc_map_events/with/key/pKdYziVhD9mH4gce0Odd-KYga4f6e9EOES1zlqFZjh1"
IMGBB_API_KEY = "e91681dfbd5603c4ee3e7030945eeaf0"
BASE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "arcevents.png")

def get_events():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        return None

def filter_events_for_hour(data, target_time):
    """
    Filters events that start within the target hour.
    target_time should be a datetime object representing the start of the hour (UTC).
    """
    upcoming_events = []
    if not data or 'data' not in data:
        return upcoming_events

    # Calculate the start and end timestamps for the target hour (in milliseconds)
    target_start_ms = int(target_time.timestamp() * 1000)
    target_end_ms = int((target_time + timedelta(hours=1)).timestamp() * 1000)

    for item in data['data']:
        name = item.get('name')
        map_name = item.get('map')
        start_time_ms = item.get('startTime')
        end_time_ms = item.get('endTime')

        # Check if event starts within the target hour
        if start_time_ms and target_start_ms <= start_time_ms < target_end_ms:
            # Convert timestamps to readable format for display
            start_dt = datetime.fromtimestamp(start_time_ms / 1000, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(end_time_ms / 1000, tz=timezone.utc)
            upcoming_events.append({
                "name": name,
                "map": map_name,
                "start": start_dt.strftime("%H:%M"),
                "end": end_dt.strftime("%H:%M")
            })
    return upcoming_events

def format_message(events, display_time_str):
    if not events:
        return f"No map events starting at {display_time_str}."
    
    return f"🗺️ ARC Raiders Map Events starting now! ({display_time_str})"

def generate_event_image(events, display_time_str):
    """
    Generate an image with event data overlaid on the base image.
    Returns the path to the generated image.
    """
    # Load the base image
    img = Image.open(BASE_IMAGE_PATH)
    draw = ImageDraw.Draw(img)
    
    # Get image dimensions
    width, height = img.size
    
    # Try to use Impact font for bold headlines
    try:
        # Use Impact font with larger sizes for social media visibility
        title_font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 40)
        event_font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 38)
        map_font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 30)
    except OSError:
        try:
            # Linux fallback
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf", 40)
            event_font = ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf", 38)
            map_font = ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/Impact.ttf", 30)
        except OSError:
            try:
                # Another Linux path
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                event_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
                map_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
            except OSError:
                # Final fallback
                title_font = ImageFont.load_default()
                event_font = ImageFont.load_default()
                map_font = ImageFont.load_default()
    
    # Prepare the text
    title = f"EVENTS STARTING AT {display_time_str.upper()}"
    
    # Calculate center position for text
    center_x = width // 2
    start_y = height // 4  # Start higher up
    
    # Draw title centered with accent color #2fff7e
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = center_x - title_width // 2
    draw.text((title_x, start_y), title, font=title_font, fill=(47, 255, 126))
    
    # Draw a subtle separator line
    line_y = start_y + 70
    line_margin = 100  # Increased margin to keep line inside text area
    draw.line([(line_margin, line_y), (width - line_margin, line_y)], fill=(255, 255, 255, 128), width=2)
    
    # Draw events with better spacing
    y_offset = start_y + 100
    for i, event in enumerate(events):
        event_text = event['name']
        map_text = f"on {event['map']}"
        
        # Event name - white
        event_bbox = draw.textbbox((0, 0), event_text, font=event_font)
        event_width = event_bbox[2] - event_bbox[0]
        event_x = center_x - event_width // 2
        draw.text((event_x, y_offset), event_text, font=event_font, fill=(255, 255, 255))
        
        y_offset += 48
        
        # Map name - cyan color #2ffeff
        map_bbox = draw.textbbox((0, 0), map_text, font=map_font)
        map_width = map_bbox[2] - map_bbox[0]
        map_x = center_x - map_width // 2
        draw.text((map_x, y_offset), map_text, font=map_font, fill=(47, 254, 255))
        
        y_offset += 65  # More spacing between events
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    # Also save a copy locally for debugging
    debug_path = os.path.join(os.path.dirname(__file__), "generated_event_image.png")
    img.save(debug_path, 'PNG')
    print(f"Debug image saved to: {debug_path}")
    
    return temp_file.name

def upload_image_to_imgbb(image_path):
    """
    Upload an image to imgbb and return the public URL.
    """
    try:
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": IMGBB_API_KEY,
                "image": image_data,
                "name": f"arc_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            image_url = result['data']['url']
            print(f"Image uploaded successfully: {image_url}")
            return image_url
        else:
            print(f"Failed to upload image: {result}")
            return None
            
    except requests.RequestException as e:
        print(f"Error uploading image: {e}")
        return None
    finally:
        # Clean up temp file
        try:
            os.unlink(image_path)
        except:
            pass

def send_webhook(message, image_url=None):
    payload = {"value1": message}
    if image_url:
        payload["value2"] = image_url
    
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
    display_time_str = target_time_est.strftime("%I:00 %p %Z")
    
    print(f"Checking events for: {target_hour_str} UTC ({display_time_str})")

    data = get_events()
    if data:
        events = filter_events_for_hour(data, target_time)
        message = format_message(events, display_time_str)
        print("Generated Message:")
        print(message)
        
        if events:
            # Generate image with event data
            print("Generating event image...")
            image_path = generate_event_image(events, display_time_str)
            
            # Upload image to imgbb
            print("Uploading image to imgbb...")
            image_url = upload_image_to_imgbb(image_path)
            
            # Send webhook with message and image URL
            send_webhook(message, image_url)
        else:
            print("No events found, skipping webhook.")

if __name__ == "__main__":
    main()
