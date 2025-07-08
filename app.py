from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
CAIRO = pytz.timezone("Africa/Cairo")

def fetch_from_ff_json():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        events = resp.json()

        now_utc = datetime.now(pytz.utc)
        today_cairo = now_utc.astimezone(CAIRO).date()
        results = []

        for ev in events:
            try:
                if ev.get("impact", "").lower() != "high":
                    continue

                dt = datetime.fromisoformat(ev["date"])
                if not dt.tzinfo:
                    dt = pytz.utc.localize(dt)

                dt_cairo = dt.astimezone(CAIRO)
                if dt_cairo.date() != today_cairo:
                    continue

                results.append({
                    "time": dt_cairo.strftime("%Y.%m.%d %H:%M"),
                    "currency": ev.get("country", ""),
                    "title": ev.get("title", ""),
                    "impact": "high"
                })
            except Exception:
                continue

        results.sort(key=lambda x: x["time"])
        return results
    except Exception as e:
        app.logger.error("Fetch error: %s", e)
        return []

@app.route("/news")
def get_news():
    data = fetch_from_ff_json()
    return jsonify({
        "status": "success",
        "count": len(data),
        "data": data,
        "server_time": datetime.now(CAIRO).strftime("%Y.%m.%d %H:%M:%S")
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
