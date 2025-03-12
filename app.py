from flask import Flask, render_template, request, jsonify
from datetime import datetime
import pytz

app = Flask(__name__)

alarm_time = None
alarm_active = True  # 追蹤鬧鐘是否啟動

@app.route("/")
def index():
    # 獲取目前台北時間
    taipei_tz = pytz.timezone('Asia/Taipei')
    current_time = datetime.now(taipei_tz).strftime('%Y-%m-%d %H:%M:%S')

    # 設定其他城市的時區
    cities = {
        'New York': 'America/New_York',
        'London': 'Europe/London',
        'Tokyo': 'Asia/Tokyo',
        'Sydney': 'Australia/Sydney',
    }

    world_times = {}
    for city, timezone in cities.items():
        tz = pytz.timezone(timezone)
        world_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        world_times[city] = world_time

    return render_template("index.html", current_time=current_time, world_times=world_times)
@app.route("/world_time")
def world_time():
    timezone = request.args.get('timezone', 'Asia/Taipei')  # 默認為台北時區
    tz = pytz.timezone(timezone)
    time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({"time": time})

@app.route("/set_alarm", methods=["POST"])
def set_alarm():
    global alarm_time, alarm_active
    data = request.json
    alarm_time = data.get("time")
    alarm_active = True  # 設定新鬧鐘時，啟動鬧鐘
    return jsonify({"status": "success", "alarm_time": alarm_time})

@app.route("/get_alarm")
def get_alarm():
    return jsonify({"alarm_time": alarm_time, "alarm_active": alarm_active})

@app.route("/stop_alarm", methods=["POST"])
def stop_alarm():
    global alarm_active
    alarm_active = False  # 停止鬧鐘
    return jsonify({"status": "stopped"})

if __name__ == "__main__":
    app.run(debug=True)
