from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta
import pytz
import logging

app = Flask(__name__)
CAIRO = pytz.timezone("Africa/Cairo")

# تهيئة نظام التسجيل (Logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_from_ff_json():
    """
    جلب بيانات الأحداث الاقتصادية من المصدر الخارجي
    مع معالجة محسنة للأخطاء والتحقق من البيانات
    """
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        
        # إضافة headers لتجنب حظر الطلبات
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Fetching data from: {url}")
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()  # يرفع استثناء إذا كان هناك خطأ في HTTP
        
        events = resp.json()
        if not isinstance(events, list):
            logger.error("Unexpected data format: Expected list, got %s", type(events))
            return []

        now_utc = datetime.now(pytz.utc)
        week_later = now_utc + timedelta(days=7)
        results = []

        for ev in events:
            try:
                # التحقق من وجود بيانات صحيحة في الحدث
                if not isinstance(ev, dict):
                    continue
                    
                if ev.get("impact", "").lower() != "high":
                    continue
                
                if "date" not in ev:
                    continue
                
                # معالجة التاريخ مع تحسينات الأمان
                dt = datetime.fromisoformat(ev["date"].replace('Z', '+00:00'))
                if not dt.tzinfo:
                    dt = pytz.utc.localize(dt)
                
                # التحقق من النطاق الزمني
                if not (now_utc <= dt <= week_later):
                    continue

                # تحويل الوقت إلى توقيت القاهرة
                dt_cairo = dt.astimezone(CAIRO)
                
                results.append({
                    "time": dt_cairo.strftime("%Y.%m.%d %H:%M"),
                    "currency": ev.get("country", "N/A"),
                    "title": ev.get("title", "No Title"),
                    "impact": "high"
                })
            except Exception as e:
                logger.warning(f"Error processing event: {ev}. Error: {str(e)}")
                continue

        # ترتيب النتائج حسب الوقت
        results.sort(key=lambda x: x["time"])
        logger.info(f"Found {len(results)} high-impact events")
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    
    return []  # إرجاع قائمة فارغة في حالة الخطأ

@app.route("/news")
def get_news():
    """
    نقطة النهاية (endpoint) لاسترجاع الأخبار الاقتصادية
    """
    try:
        data = fetch_from_ff_json()
        response = {
            "status": "success",
            "count": len(data),
            "data": data,
            "server_time": datetime.now(CAIRO).strftime("%Y.%m.%d %H:%M:%S"),
            "time_range": {
                "start": datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "end": (datetime.now(pytz.utc) + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in /news endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "server_time": datetime.now(CAIRO).strftime("%Y.%m.%d %H:%M:%S")
        }), 500

if __name__ == "__main__":
    # تشغيل الخادم مع إعدادات محسنة
    app.run(
        host="0.0.0.0",
        port=10000,
        threaded=True,
        debug=False  # في الإنتاج يجب أن يكون False
    )
