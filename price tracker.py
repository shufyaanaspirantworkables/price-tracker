import os
import csv
import time
import ssl
import smtplib
import requests
import schedule
from datetime import datetime
from email.message import EmailMessage
from bs4 import BeautifulSoup

import config

# ---------- Settings ----------
GBP_TO_INR = 129.0      # update from Google before running
TARGET_PRICE = 3000     # alert threshold in rupees
CHECK_EVERY_MINUTES = 60# use a bigger number for real use
FILE = "prices_inr.csv"
URL = "https://books.toscrape.com/"


def load_last_prices():
    """Read the CSV and return {title: most recent price}."""
    last = {}
    if os.path.exists(FILE):
        with open(FILE, "r", newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                last[row[1]] = float(row[2])
    return last


def send_email(subject, body):
    """Send a plain-text email through Gmail."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_ADDRESS
    msg["To"] = config.RECEIVER
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
        server.send_message(msg)


def check_prices():
    """Scrape the site, compare with last prices, save and report."""
    previous = load_last_prices()

    try:
        response = requests.get(URL, timeout=10)
        response.encoding = "utf-8"
    except requests.RequestException as e:
        print("Could not reach the website:", e)
        return

    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("article", class_="product_pod")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deals, drops, rises = [], [], []

    with open(FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for book in books:
            title = book.h3.a["title"]
            price_text = book.find("p", class_="price_color").text
            price_gbp = float(price_text.replace("£", ""))
            price_inr = round(price_gbp * GBP_TO_INR, 2)

            writer.writerow([now, title, price_inr])

            if price_inr <= TARGET_PRICE:
                deals.append((title, price_inr))

            old_price = previous.get(title)
            if old_price is not None:
                if price_inr < old_price:
                    drops.append((title, old_price, price_inr))
                elif price_inr > old_price:
                    rises.append((title, old_price, price_inr))

    print(f"\n[{now}] Checked {len(books)} books")
    print(f"Under your target (₹{TARGET_PRICE}): {len(deals)} book(s)")

    for title, old, new in drops:
        percent = (old - new) / old * 100
        print(f"  DROP: {title}: ₹{old:.2f} -> ₹{new:.2f} (-{percent:.1f}%)")

    for title, old, new in rises:
        percent = (new - old) / old * 100
        print(f"  RISE: {title}: ₹{old:.2f} -> ₹{new:.2f} (+{percent:.1f}%)")

    if not drops and not rises:
        print("No price changes since last run.")

    if drops:
        lines = [f"{t}: ₹{o:.2f} -> ₹{n:.2f}" for t, o, n in drops]
        try:
            send_email(f"Price drop: {len(drops)} book(s)", "\n".join(lines))
            print("Email sent")
        except Exception as e:
            print("Email failed:", e)


schedule.every(CHECK_EVERY_MINUTES).minutes.do(check_prices)

check_prices()

print("Tracker running. Press the stop button to quit.")
while True:
    schedule.run_pending()
    time.sleep(1)