from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import json

app = Flask(__name__)

CAIRO = pytz.timezone("Africa/Cairo")

def fetch_forex_factory_news():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "xml")
        results = []
        now = datetime.now(pytz.utc)
        week_later = now + timedelta(days=7)

        for item in soup.find_all("event"):
            try:
                impact = item.impact.text.strip().lower()
                if impact != "high":
                    continue

                currency = item.currency.text.strip()
                date_str = item.date.text.strip()
                time_str = item.time.text.strip()

                # Parse and convert to Cairo time
                dt = datetime.strptime(f"{date_str} {time_str}", "%b %d %Y %I:%M%p")
                dt = pytz.utc.localize(dt).astimezone(CAIRO)
                
                # Only include upcoming news (within 7 days)
                if dt.tzinfo.localize(dt) < now or dt > week_later:
                    continue

                results.append({
                    "time": dt.strftime("%Y.%m.%d %H:%M"),  # MT4 compatible format
                    "currency": currency,
                    "title": item.title.text.strip() if item.title else "",
                    "impact": impact
                })

            except Exception as e:
                app.logger.error(f"Error processing event: {e}")
                continue

        # Sort by time
        results.sort(key=lambda x: x["time"])
        return results

    except Exception as e:
        app.logger.error(f"Error fetching news: {e}")
        return []

@app.route("/news")
def get_news():
    try:
        data = fetch_forex_factory_news()
        return jsonify({
            "status": "success",
            "data": data,
            "count": len(data),
            "server_time": datetime.now(CAIRO).strftime("%Y.%m.%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
