from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# المنطقة الزمنية المطلوبة
CAIRO = pytz.timezone("Africa/Cairo")

# العملات المسموح بها وفترات الحظر الخاصة بها (بالدقائق)
BLOCK_CONFIG = {
    "USD": {"before": 30, "after": 30},
    "EUR": {"before": 15, "after": 10},
    "CAD": {"before": 20, "after": 20}
}

ALLOWED_CURRENCIES = set(BLOCK_CONFIG.keys())

# جلب الأخبار من موقع Investing
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

            if impact == "3" and currency in ALLOWED_CURRENCIES:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                dt = pytz.utc.localize(dt).astimezone(CAIRO)

                block = BLOCK_CONFIG.get(currency, {"before": 30, "after": 30})

                results.append({
                    "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "currency": currency,
                    "impact": "High",
                    "block_before": block["before"],
                    "block_after": block["after"]
                })
        except Exception:
            continue

    return results

# Endpoint الأساسي
@app.route("/news")
def get_news():
    try:
        data = fetch_investing_news()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# التشغيل على Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
