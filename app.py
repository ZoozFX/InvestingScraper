from flask import Flask, jsonify, request
import requests
from datetime import datetime, timedelta
import pytz
import os
import json

app = Flask(__name__)
CAIRO = pytz.timezone("Africa/Cairo")
CACHE_FILE = "cached_news.json"
SECRET_KEY = "my_secret_123"  # ← غيّر هذا المفتاح

def is_cache_fresh():
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)
            cache_time = datetime.strptime(data.get("cache_time", ""), "%Y-%m-%d").date()
            return cache_time == datetime.now(CAIRO).date()
    except:
        return False

def load_cache():
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
        return data.get("data", [])

def save_cache(news_list):
    with open(CACHE_FILE, "w") as f:
        json.dump({
            "cache_time": datetime.now(CAIRO).strftime("%Y-%m-%d"),
            "data": news_list
        }, f, indent=2)

def fetch_from_ff_json():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        events = resp.json()

        now_utc = datetime.now(pytz.utc)
        today_cairo = now_utc.astimezone(CAIRO).date()
        results = []

        for ev in events:
            try:
                impact = ev.get("impact", "").lower()
                if impact not in ["high", "medium", "low"]:
                    continue  # تجاهل أي قيم غير معروفة

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
                    "impact": impact
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
    if not is_cache_fresh() and os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

    if is_cache_fresh():
        data = load_cache()
    else:
        data = fetch_from_ff_json()
        save_cache(data)

    return jsonify({
        "status": "success",
        "count": len(data),
        "data": data,
        "server_time": datetime.now(CAIRO).strftime("%Y.%m.%d %H:%M:%S")
    }), 200

@app.route("/refresh")
def refresh_cache():
    user_key = request.args.get("key")
    if user_key != SECRET_KEY:
        return jsonify({"status": "unauthorized", "message": "Invalid or missing API key."}), 401

    try:
        # حذف الملف إذا كان موجود
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        
        # جلب الأخبار وتخزينها
        data = fetch_from_ff_json()
        save_cache(data)

        return jsonify({
            "status": "success",
            "message": "Cache refreshed and data reloaded.",
            "count": len(data),
            "data": data,
            "server_time": datetime.now(CAIRO).strftime("%Y.%m.%d %H:%M:%S")
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to refresh cache: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
