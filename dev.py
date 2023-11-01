import os
import io
import time

from cs50 import SQL
import json
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    make_response,
    send_file,
)
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Import date class from datetime module
import datetime, pdfkit

from num2words import num2words

from helpers import (
    apology,
    login_required,
    inr,
    is_valid_phno,
    is_valid_email,
    is_valid_password,
    is_valid_pncd,
    bill_num_formatr,
)

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

"""Fetch and convert state_codes from db"""
# Fetches state_codes from db as list of dicts
db_state_codes = db.execute("SELECT * FROM state_codes")

# Converts db_state_codes to dict where key is state_name and value is dict of key tin and key state_code
state_codes = {}
for i in db_state_codes:
    state_codes[i["state_name"]] = {"tin": i["tin"], "state_code": i["state_code"]}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


activepage = " active"


@app.route("/inventory")
@login_required
def inventory():
    """Show Inventory of goods and beneficiaries of the company"""
    start = time.time()
    goods_query = """
    SELECT
        g.descp,
        g.hsn_sac,
        g.uom,
        g.rate,
        g.gst,
        g.added_at,
        u1.username AS added_by
    FROM
        goods AS g
        JOIN users AS u1 ON g.added_by = u1.id
    WHERE
        g.company_id = ?
    ORDER BY
        g.id DESC;
    """
    clients_query = """
    SELECT
        b.name,
        b.addrBnm,
        b.addrBno,
        b.addrFlno,
        b.addrSt,
        b.addrLoc,
        b.addrDist,
        b.addrState,
        b.addrPncd,
        b.phno1,
        b.phno2,
        b.gstin,
        b.added_at,
        u2.username AS added_by
    FROM
        beneficiaries AS b
        JOIN users AS u2 ON b.added_by = u2.id
    WHERE
        b.company_id = ?
    ORDER BY
        b.id DESC;
    """

    try:
        goods_list = db.execute(goods_query, session["company_id"])
        clients_list = db.execute(clients_query, session["company_id"])
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: INVN-MAT-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    optional_goods_fields = ("hsn_sac", "uom")
    for good in goods_list:
        good.update(
            {
                k: good[k] or ""
                for k in optional_goods_fields
            }
        )

    address_fields = (
        "addrBnm",
        "addrBno",
        "addrFlno",
        "addrSt",
        "addrLoc",
        "addrDist",
        "addrPncd",
        "addrState",
    )
    phno_fields = ("phno1", "phno2")
    optional_clients_fields = ("gstin",)
    for client in clients_list:
        client["addr"] = " ".join(
            client[field] for field in address_fields if client[field]
        )
        client["phno"] = ", ".join(
            client[field] for field in phno_fields if client[field]
        )
        client.update(
            {
                k: client[k] or ""
                for k in optional_clients_fields
            }
        )

    end = time.time()
    print(end - start)
    return render_template(
        "inventory.html",
        clients_list=clients_list,
        goods_list=goods_list,
        inventorynav=activepage,
    )
