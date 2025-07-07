from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

app = Flask(__name__)

CAIRO = pytz.timezone("Africa/Cairo")

def fetch_forex_factory_news():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "xml")

    results = []

    items = soup.find_all("event")

    for item in items:
        try:
            impact = item.impact.text.strip()
            currency = item.currency.text.strip()
            date_str = item.date.text.strip()
            time_str = item.time.text.strip()

            if impact.lower() != "high":
                continue  # فقط الأخبار ذات التأثير العالي

            # تكوين التاريخ والوقت الكامل
            full_str = f"{date_str} {time_str}"
            dt = datetime.strptime(full_str, "%b %d %Y %I:%M%p")
            dt = pytz.utc.localize(dt).astimezone(CAIRO)

            results.append({
                "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "currency": currency,
                "impact": impact
            })

        except Exception as e:
            continue

    return results

@app.route("/news")
def get_news():
    try:
        data = fetch_forex_factory_news()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
