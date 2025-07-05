from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# ====== بيانات وهمية ثابتة (للاختبار) ======
def fetch_investing_news():
    return [
        {"time": "2025-07-05 12:00:00", "currency": "USD", "impact": "High"},
        {"time": "2025-07-05 14:00:00", "currency": "EUR", "impact": "High"},
        {"time": "2025-07-05 16:30:00", "currency": "CAD", "impact": "High"}
    ]

# ====== Endpoint الأساسي ======
@app.route("/news")
def get_news():
    try:
        data = fetch_investing_news()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ====== التشغيل على Render ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
