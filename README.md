# ARC Raiders Event Tracker

This script fetches ARC Raiders map events from the MetaForge API and sends a notification to an IFTTT Webhook for events starting in the coming hour.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

2.  **Configuration:**
    The script is configured in `arc_event_tracker.py`.
    - `IFTTT_KEY`: Your IFTTT Webhook key.
    - `IFTTT_EVENT_NAME`: The event name used in your IFTTT Applet (currently set to `arc_map_events`).

## Usage

Run the script manually:
```bash
python3 arc_event_tracker.py
```

## Automation (Cron)

To run this script automatically at the top of every hour:

1.  **Make the helper script executable:**
    ```bash
    chmod +x run_tracker.sh
    ```

2.  **Add to Crontab:**
    Run this command in your terminal to schedule the job:
    ```bash
    (crontab -l 2>/dev/null; echo "0 * * * * /bin/bash '/Users/zach/Library/Mobile Documents/com~apple~CloudDocs/arceventtracker/run_tracker.sh'") | crontab -
    ```

    This will run the script at minute 0 of every hour.
    Output will be logged to `cron_log.txt`.

## IFTTT Setup

1.  Create a new Applet in IFTTT.
2.  **If This:** Select **Webhooks**.
3.  Choose **Receive a web request**.
4.  Enter the Event Name: `arc_map_events`.
5.  **Then That:** Select **Twitter** (or your desired service).
6.  Choose **Post a tweet**.
7.  In the Tweet text, use the ingredient `Value1` (which will contain the message formatted by this script).
