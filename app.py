import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, inr  # validate_phno  # lookup

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["inr"] = inr

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///circusledger.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        loguser = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(loguser) != 1 or not check_password_hash(
            loguser[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = loguser[0]["id"]
        session["company_id"] = loguser[0]["company_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        regusername = request.form.get("username")
        if not regusername:
            return apology("Username not provided")

        # Query database for username
        reguser = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Check username exists
        if len(reguser) == 1:
            return apology("Username already exsists")

        # Ensure password was submitted
        regemail = request.form.get("email")
        if not regemail:
            return apology("must provide Email Address")

        # Ensure password was submitted
        regpassword = request.form.get("password")
        if not regpassword:
            return apology("must provide password")

        # Ensure confirmation was submitted
        regconfirm = request.form.get("confirmation")
        if not regconfirm:
            return apology("must provide password (again)")

        if not regpassword == regconfirm:
            return apology("password must be same")

        regid = db.execute(
            "INSERT INTO users (username, email, hash, phno, type) VALUES(?, ?, ?, ?, ?)",
            regusername,
            regemail,
            generate_password_hash(regpassword),
            request.form.get("phno"),
            "admin",
        )

        # Remember which user has logged in
        session["user_id"] = regid

        # Redirect user to home page
        flash("User successfully registered")
        return redirect("/compregister")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/compregister", methods=["GET", "POST"])
def compregister():
    """Register company"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        compreg = {}

        # NOT NULL fields
        # Ensure company name was submitted
        compreg["name"] = request.form.get("name")
        if not compreg["name"]:
            return apology("Company name not provided")

        # Ensure Address:Building number was submitted
        compreg["addrBno"] = request.form.get("addrBno")
        if not compreg["addrBno"]:
            return apology("Address: Building number not provided")

        # Ensure Address:Street name was submitted
        compreg["addrSt"] = request.form.get("addrSt")
        if not compreg["addrSt"]:
            return apology("Address: Street name not provided")

        # Ensure Address:Area/Town was submitted
        compreg["addrLoc"] = request.form.get("addrLoc")
        if not compreg["addrLoc"]:
            return apology("Address: Area/Town not provided")

        # Ensure Address:City/District was submitted
        compreg["addrDist"] = request.form.get("addrDist")
        if not compreg["addrDist"]:
            return apology("Address: City/District not provided")

        # Ensure Address:State was submitted
        compreg["addrState"] = request.form.get("addrState")
        if not compreg["addrState"]:
            return apology("Address: State not provided")

        # Ensure Address:Pincode was submitted
        compreg["addrPncd"] = request.form.get("addrPncd")
        if not compreg["addrPncd"]:
            return apology("Address: Pincode not provided")

        # Ensure Mobile number was submitted
        compreg["phno1"] = request.form.get("phno1")
        if not compreg["phno1"]:
            return apology("Mobile number not provided")

        # Ensure GSTIN was submitted
        compreg["gstin"] = request.form.get("gstin")
        if not compreg["gstin"]:
            return apology("GSTIN not provided")

        # Can be NULL fields
        # Collect all the optional fields
        compreg["addrBnm"] = request.form.get("addrBnm")
        compreg["Flno"] = request.form.get("Flno")
        compreg["phno2"] = request.form.get("phno2")
        compreg["email"] = request.form.get("email")
        compreg["website"] = request.form.get("website")
        compreg["bnkAcnm"] = request.form.get("bnkAcnm")
        compreg["bnkAcno"] = request.form.get("bnkAcno")
        compreg["bnkNm"] = request.form.get("bnkNm")
        compreg["bnkIfsc"] = request.form.get("bnkIfsc")

        # UNIQUE fields

        # Check for a valid mobile number
        valid = validate_phno(compreg["phno1"])
        if not valid:
            return apology("Invalid mobile number")

        # Done until here

        # Query database for phno1
        compregphno1 = db.execute(
            "SELECT * FROM companies WHERE phno1 = ?", request.form.get("phno1")
        )

        # Check username exists
        if len(compregphno1) == 1:
            return apology("Username already exsists")

        # Ensure password was submitted
        regemail = request.form.get("email")
        if not regemail:
            return apology("must provide Email Address")

        # Ensure password was submitted
        regpassword = request.form.get("password")
        if not regpassword:
            return apology("must provide password")

        # Ensure confirmation was submitted
        regconfirm = request.form.get("confirmation")
        if not regconfirm:
            return apology("must provide password (again)")

        if not regpassword == regconfirm:
            return apology("password must be same")

        regid = db.execute(
            "INSERT INTO users (username, email, hash, phno, type) VALUES(?, ?, ?, ?, ?)",
            regusername,
            regemail,
            generate_password_hash(regpassword),
            request.form.get("phno"),
            "admin",
        )

        # Remember which user has logged in
        session["user_id"] = regid

        # Redirect user to home page
        flash("User successfully registered")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("compregister.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")
