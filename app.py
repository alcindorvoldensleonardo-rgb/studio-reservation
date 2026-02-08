from flask import Flask, render_template, request, redirect, session
from flask import jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request
import sqlite3
import hashlib
import smtplib
import stripe
import os
import json
import stripe

app = Flask(__name__)
app.secret_key = "secret123"
stripe.api_key = "sk_test_51QhH4XPBry1od3dSTcQURRRUE3GWu1IiltE1xh8kX5kvkuFK55YpsSoXdWvHm1i9h7RaNxaxZTQfYf90j6C2kGv300aa9ZxVCN"
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

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

@app.route("/confirmation")
def confirmation():
    return render_template("confirmation.html")

@app.route("/payment-success")
def payment_success():
    return render_template("payment_success.html")
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    return "ROUTE OK"    
            
#dashboard============================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM reservations ORDER BY date, time")
    data = c.fetchall()
    conn.close()

    return render_template("dashboard.html", data=data)
#enddashboardcode================================

@app.route("/delete/<int:id>")
def delete_reservation(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")
    
#emailconf.=========================================
def send_confirmation_email(to_email, name, date, time):
    sender_email = "vlastudio@gmail.com"
    sender_password = "vla1234$"

    subject = "📸 Réservation confirmée – Studio Photo"

    body = f"""
Bonjour {name},

✅ Votre réservation est confirmée !

📅 Date : {date}
⏰ Heure : {time}

Merci d’avoir choisi notre studio photo.
À très bientôt 📸✨

— Studio Photo
"""

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Erreur email :", e)
#endconfemail===================================================
#stripe============================================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
#endstripe==============================================

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    # ✅ Paiement confirmé
    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]

        name = session_data["metadata"]["name"]
        email = session_data["metadata"]["email"]
        date = session_data["metadata"]["date"]
        time = session_data["metadata"]["time"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # éviter doublons
        c.execute(
            "SELECT * FROM reservations WHERE date=? AND time=?",
            (date, time)
        )

        if not c.fetchone():
            c.execute(
                "INSERT INTO reservations (name,email,date,time) VALUES (?,?,?,?)",
                (name, email, date, time)
            )
            conn.commit()

        conn.close()

    return "", 200

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
            return redirect("/dashboard")
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
    
      # 📧 ENVOI EMAIL
    send_confirmation_email(email, name, date, time)

    return redirect("/confirmation")
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
    app.run(host="0.0.0.0", port=10000)
