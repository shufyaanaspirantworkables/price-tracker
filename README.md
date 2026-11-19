# Automated Web Scraper & Price Tracker

Scrapes book prices from books.toscrape.com, converts them to rupees,
saves a price history to CSV, and emails an alert when prices drop.

## Features
- Scrapes titles and prices with requests and BeautifulSoup
- Converts GBP to INR using a configurable exchange rate
- Saves a timestamped price history to a CSV file
- Detects price drops and rises compared with the previous run
- Runs automatically on a schedule
- Sends Gmail alerts using an App Password

## Setup
1. pip install requests beautifulsoup4 schedule
2. Copy config_example.py to config.py and fill in your Gmail App Password
3. Set GBP_TO_INR and TARGET_PRICE in the program
4. Run the program

## Notes
- books.toscrape.com is a practice site, so price drops were tested by changing the exchange rate.
- Never upload config.py, because it holds your password.
