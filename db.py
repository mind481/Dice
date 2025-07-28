import sqlite3
from datetime import datetime

def init_db(path="stats.db"):
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL;")  # 동시성/안정성 ↑
    con.executescript("""
    CREATE TABLE IF NOT EXISTS latest_roll (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      face INTEGER NOT NULL,
      timestamp TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS daily_counts (
      date TEXT NOT NULL,
      face INTEGER NOT NULL,
      count INTEGER NOT NULL,
      PRIMARY KEY (date, face)
    );
    CREATE TABLE IF NOT EXISTS monthly_counts (
      yyyymm TEXT NOT NULL,
      face INTEGER NOT NULL,
      count INTEGER NOT NULL,
      PRIMARY KEY (yyyymm, face)
    );
    CREATE TABLE IF NOT EXISTS total_counts (
      face INTEGER PRIMARY KEY,
      count INTEGER NOT NULL
    );
    """)
    return con

def add_roll(con, face):
    con.execute("""
        INSERT INTO latest_roll (id, face, timestamp)
        VALUES (1, ?, DATETIME('now','localtime'))
        ON CONFLICT(id) DO UPDATE SET
            face = excluded.face,
            timestamp = excluded.timestamp;
    """, (face,))
    con.execute("""
        INSERT INTO daily_counts(date, face, count)
        VALUES (DATE('now','localtime'), ?, 1)
        ON CONFLICT(date, face) DO UPDATE SET count = count + 1
    """, (face,))
    con.execute("""
        INSERT INTO monthly_counts(yyyymm, face, count)
        VALUES (STRFTIME('%Y-%m','now','localtime'), ?, 1)
        ON CONFLICT(yyyymm, face) DO UPDATE SET count = count + 1
    """, (face,))
    con.execute("""
        INSERT INTO total_counts(face, count)
        VALUES (?, 1)
        ON CONFLICT(face) DO UPDATE SET count = count + 1
    """, (face,))
    con.commit()
