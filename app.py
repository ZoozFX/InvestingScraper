from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# إعداد المنطقة الزمنية حسب بلدك
CAIRO = pytz.timezone("Africa/Cairo")

# ====== دالة جلب الأخبار من Investing.com ======
def fetch_investing_news():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url = "https://www.investing.com/economic-calendar/"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    results = []

    rows = soup.find_all("tr", {"class": "js-event-item"})

    for row in rows:
        try:
            impact = row["data-impact"]
            currency = row["data-ev-curr"]
            time_str = row["data-event-datetime"]

            if impact == "3":  # التأثير العالي فقط
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                dt = pytz.utc.localize(dt).astimezone(CAIRO)
                results.append({
                    "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "currency": currency,
                    "impact": "High"
                })
        except Exception:
            continue

    return results

# ====== API Endpoint ======
@app.route("/news")
def get_news():
    try:
        data = fetch_investing_news()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====== تشغيل التطبيق على Render ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
