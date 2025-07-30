from flask import Flask, render_template
from datetime import datetime
import sqlite3

app = Flask(__name__)

def get_db():
    return sqlite3.connect("stats.db")

@app.route("/")
def index():
    con = get_db()
    cur = con.cursor()

    # 최근값
    cur.execute("SELECT face, timestamp FROM latest_roll")
    latest = cur.fetchone()
    latest_face = latest[0] if latest else "?"
    latest_time = latest[1] if latest else "?"

    # 통계
    def get_stats(query):
        cur.execute(query)
        result = cur.fetchall()
        stats = {str(i): 0 for i in range(1, 7)}
        for face, count in result:
            stats[str(face)] = count
        return stats

    today = str(datetime.today()).split(" ")[0]
    daily = get_stats("SELECT face, count FROM daily_counts WHERE date = DATE('now','localtime')")
    monthly = get_stats("SELECT face, count FROM monthly_counts WHERE yyyymm = STRFTIME('%Y-%m','now','localtime')")
    total = get_stats("SELECT face, count FROM total_counts")
    total_count = sum(total.values())

    con.close()

    return render_template("index.html",
                           latest_face=latest_face,
                           latest_time=latest_time,
                           today=today,
                           daily=daily,
                           monthly=monthly,
                           total=total,
                           total_count=total_count)

if __name__ == '__main__':
    app.run(debug=True)