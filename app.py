from flask import Flask, render_template, Response
import time
from datetime import datetime
import sqlite3
import signal
import sys

app = Flask(__name__)

def get_db():
    return sqlite3.connect("stats.db")

def get_cursor(con):
    return con.cursor()

def get_latest_stat(cur):
    cur.execute("SELECT face FROM latest_roll")
    latest = cur.fetchone()
    latest_face = latest[0] if latest else "?"
    return latest_face

def get_stats(cur, query):
    cur.execute(query)
    result = cur.fetchall()
    stats = [0,0,0,0,0,0]
    for face, count in result:
        stats[face-1] = count
    return stats

def event_stream():
    con = get_db()
    cur = get_cursor(con)
    try:
        _, previous_value = get_latest_stat(cur)# 현재 DB 값으로 초기화
        while True:
            _, current_value = get_latest_stat(cur)
            if current_value != previous_value:
                yield f"data: {current_value}\n\n"
                previous_value = current_value
            time.sleep(1)  # 1초마다 확인
    finally:
        con.close()

@app.route("/")
def index():
    con = get_db()
    cur = get_cursor(con)
    # 최근값
    latest_face = get_latest_stat(cur)
    daily = get_stats(cur, "SELECT face, count FROM daily_counts WHERE date = DATE('now','localtime')")
    monthly = get_stats(cur, "SELECT face, count FROM monthly_counts WHERE yyyymm = STRFTIME('%Y-%m','now','localtime')")
    total = get_stats(cur, "SELECT face, count FROM total_counts")

    con.close()

    return render_template("index.html",
                           latest_face=latest_face,
                           daily=daily,
                           monthly=monthly,
                           total=total,
                           daily_count=sum(daily),
                           monthly_count=sum(monthly),
                           total_count=sum(total)
                           )
        
@app.route('/events')
def sse():
    return Response(event_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)