from flask import Flask, render_template, request, redirect, session
from flask import jsonify
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "secret123"


def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        date TEXT,
        time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    return render_template("index.html")
    
@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

#reservationfront================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(
            request.form["password"].encode()
        ).hexdigest()

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, password)
        )
        admin = c.fetchone()
        conn.close()

        if admin:
            session["admin"] = True
            return redirect("/reservations")
        else:
            return "Login incorrect"

    return render_template("login.html")


@app.route("/reserve", methods=["POST"])
def reserve():
    name = request.form["name"]
    email = request.form["email"]
    date = request.form["date"]
    time = request.form["time"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM reservations WHERE date=? AND time=?",
        (date, time)
    )

    if c.fetchone():
        conn.close()
        return "Créneau déjà réservé"

    c.execute(
        "INSERT INTO reservations (name,email,date,time) VALUES (?,?,?,?)",
        (name, email, date, time)
    )

    conn.commit()
    conn.close()

    return redirect("/")
#endfrontreserv==================================================

#apicalendar====================================
@app.route("/api/calendar")
def api_calendar():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT date, time FROM reservations")
    data = c.fetchall()
    conn.close()
    return jsonify(data)
#endapicalendar========================================

#secureviewreservation=======================
@app.route("/reservations")
def reservations():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM reservations")
    data = c.fetchall()
    conn.close()

    return render_template("reservations.html", data=data)
#endsecurereserv===========================

#logout=========================
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")
#endlogoutcode=========================

if __name__ == "__main__":
    app.run(debug=True)