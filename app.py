from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import pytz
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# MySQL 資料庫連線配置
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'alarm_clock_db')
}
# 初始化資料庫連線
def get_db_connection():
    return mysql.connector.connect(**db_config)

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

    # 從資料庫獲取最新鬧鐘
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT alarm_time, is_active FROM alarms ORDER BY created_at DESC LIMIT 1")
    alarm = cursor.fetchone()
    cursor.close()
    conn.close()

    alarm_time = alarm['alarm_time'] if alarm else None
    alarm_active = alarm['is_active'] if alarm else False

    return render_template("index.html", current_time=current_time, world_times=world_times, alarm_time=alarm_time, alarm_active=alarm_active)

@app.route("/world_time")
def world_time():
    timezone = request.args.get('timezone', 'Asia/Taipei')
    tz = pytz.timezone(timezone)
    time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({"time": time})

@app.route("/set_alarm", methods=["POST"])
def set_alarm():
    data = request.json
    alarm_time = data.get("time")

    # 儲存鬧鐘到資料庫
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO alarms (alarm_time, is_active) VALUES (%s, %s)", (alarm_time, True))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "success", "alarm_time": alarm_time})

@app.route("/get_alarm")
def get_alarm():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT alarm_time, is_active FROM alarms ORDER BY created_at DESC LIMIT 1")
    alarm = cursor.fetchone()
    cursor.close()
    conn.close()

    alarm_time = alarm['alarm_time'] if alarm else None
    alarm_active = alarm['is_active'] if alarm else False
    return jsonify({"alarm_time": alarm_time, "alarm_active": alarm_active})

@app.route("/stop_alarm", methods=["POST"])
def stop_alarm():
    # 更新資料庫中的鬧鐘狀態
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alarms SET is_active = %s WHERE is_active = %s", (False, True))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "stopped"})

@app.route("/snooze_alarm", methods=["POST"])
def snooze_alarm():
    # 貪睡 5 分鐘
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT alarm_time FROM alarms WHERE is_active = %s ORDER BY created_at DESC LIMIT 1", (True,))
    alarm = cursor.fetchone()
    
    if alarm:
        alarm_time = datetime.strptime(alarm['alarm_time'], '%Y-%m-%d %H:%M:%S')
        new_alarm_time = (alarm_time + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE alarms SET alarm_time = %s WHERE is_active = %s", (new_alarm_time, True))
        conn.commit()
    
    cursor.close()
    conn.close()
    return jsonify({"status": "snoozed", "new_alarm_time": new_alarm_time if alarm else None})

if __name__ == "__main__":
    app.run(debug=True)
