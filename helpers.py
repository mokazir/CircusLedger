# import csv
# import datetime
# import pytz
# import requests
# import subprocess
# import urllib
# import uuid
from re import match as regexmatch

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if not session.get("company_id"):
            return redirect("/compregister")
        return f(*args, **kwargs)

    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def inr(value):
    """Format value as INR."""
    if value:
        return f"₹{value:,.2f}"


# Check a string of phone number for its length to be exactly 10 and it only contains numbers from 0-9 only
def is_valid_phno(phone_number):
    return phone_number.isdecimal() and len(phone_number) == 10


def is_valid_password(password):
    pattern = r"^(?=.*[A-Za-z\d])(?=.*[\d\W\s])(?=.*[A-Za-z\W\s])[A-Za-z\d\s\W]{8,}$"
    return regexmatch(pattern, password) is not None


def is_valid_email(email):
    pattern = r"^[\w!#$%&'*+/=?^`{|}~\.-]{1,64}@[a-zA-Z0-9.-]{1,255}\.[a-zA-Z]{2,}$"
    return regexmatch(pattern, email) is not None


def is_valid_pncd(pincode):
    pattern = r"^[1-9][0-9]{5}$"
    return regexmatch(pattern, pincode) is not None


def bill_num_formatr(bill_type, bill_timestamp, bill_num):
    current_bill_month = int(bill_timestamp[5:7])
    current_bill_year = int(bill_timestamp[2:4])
    current_bill_year = (
        f"{current_bill_year}/{current_bill_year + 1}"
        if current_bill_month > 3
        else f"{current_bill_year - 1}/{current_bill_year}"
    )
    current_bill_type = "INV" if bill_type == "Invoice" else "EST"
    return f"{current_bill_type}-{current_bill_year}-{str(current_bill_month).zfill(2)}-{str(bill_num).zfill(6)}"


"""
def lookup(symbol):
    # Look up quote for symbol.

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"User-Agent": "python-requests", "Accept": "*/*"},
        )
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)
        return {"name": symbol, "price": price, "symbol": symbol}
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None
"""
