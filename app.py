import os
import io

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
    validate_phno,
    validate_email,
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


@app.route("/")
@login_required
def index():
    def fetch_data(type):
        query = """
        SELECT
            h.id,
            CASE
                WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
                ELSE 'EST-' || h.bill_num
            END AS bill_num,
            h.bill_timestamp,
            COALESCE(b1.name, '') AS billed_to,
            COALESCE(b2.name, '') AS shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount,
            json_group_array (
                json_object (
                    'descp',
                    g.descp,
                    'hsn_sac',
                    g.hsn_sac,
                    'uom',
                    g.uom,
                    'rate',
                    g.rate,
                    'gst',
                    g.gst,
                    'qty',
                    hg.qty
                )
            ) AS list_of_goods
        FROM
            history AS h
            LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
            LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
            LEFT JOIN history_goods AS hg ON h.id = hg.history_id
            LEFT JOIN goods AS g ON hg.goods_id = g.id
        WHERE
            h.company_id = ?
            AND h.type = ?
        GROUP BY
            h.id,
            h.bill_num,
            h.bill_timestamp,
            billed_to,
            shipped_to,
            h.transport,
            h.payment,
            h.eta,
            h.amount
        ORDER BY
            h.id DESC
        LIMIT
            5;
        """

        result = db.execute(query, session["company_id"], type)

        return result

    invoice_list = fetch_data("Invoice")
    quotation_list = fetch_data("Quotation")

    # Process the list_of_goods field to convert it from a string to a JSON object
    for item in invoice_list + quotation_list:
        item["list_of_goods"] = json.loads(item["list_of_goods"])

    return render_template(
        "index.html",
        invoice_list=invoice_list,
        quotation_list=quotation_list,
        homenav=activepage,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        loguser = db.execute("SELECT * FROM users WHERE username = ?", username)
        # print(loguser)

        # Ensure username exists and password is correct
        if len(loguser) != 1 or not check_password_hash(loguser[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in and which company he belongs to
        session["user_id"] = loguser[0]["id"]
        session["company_id"] = loguser[0]["company_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", loginnav=activepage)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/invoice", methods=["GET", "POST"])
@login_required
def invoice():
    """Generate a invoice and send it to the user"""

    # Get the last invoice number which is in the format of financial years-month-six digit number
    invoice_num = db.execute(
        "SELECT bill_num FROM history WHERE company_id = ? and type = ? ORDER BY id DESC LIMIT 1",
        session["company_id"],
        "Invoice",
    )

    # Reset the invoice number every year on the 1st of April
    current_date = datetime.date.today()

    if len(invoice_num) == 0:
        invoice_num = 1
        if current_date.month < 4:
            year = current_date.year - 1
        else:
            year = current_date.year

    else:
        if current_date.month < 4:
            year = current_date.year - 1
            invoice_num = int(invoice_num[0]["bill_num"][-6:]) + 1

        else:
            year = current_date.year
            if invoice_num[0]["bill_num"][3:5] == str(current_date.year):
                invoice_num = 1
            else:
                invoice_num = int(invoice_num[0]["bill_num"][-6:]) + 1

    invoice_num_db = f"{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(invoice_num).zfill(6)}"
    invoice_num_formatted = f"INV-{invoice_num_db}"
    IN_format = current_date.strftime("%d/%m/%Y")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        invoicedata = request.form
        # print(invoicedata)

        company = db.execute(
            "SELECT * FROM companies WHERE id = ?", session["company_id"]
        )
        company = company[0]
        company["addr"] = (
            company["addrBnm"]
            + " "
            + company["addrBno"]
            + " "
            + company["addrFlno"]
            + " "
            + company["addrSt"]
            + " "
            + company["addrLoc"]
            + " "
            + company["addrDist"]
            + "-"
            + company["addrPncd"]
            + " "
            + company["addrState"]
        )
        company["phno"] = company["phno1"] + ", " + company["phno2"]

        invoicedata1 = {}

        # Temporarily Create Sgstin Number
        invoicedata1["sgstin"] = "8975463213079854"

        invoicedata1["baddr"] = (
            invoicedata["baddrBnm"]
            + " "
            + invoicedata["baddrBno"]
            + " "
            + invoicedata["baddrFlno"]
            + " "
            + invoicedata["baddrSt"]
            + " "
            + invoicedata["baddrLoc"]
            + " "
            + invoicedata["baddrDist"]
            + "-"
            + invoicedata["baddrPncd"]
            + " "
            + invoicedata["baddrState"]
        )

        invoicedata1["bphno"] = invoicedata["bphno"] + ", " + invoicedata["bphno1"]

        invoicedata1["saddr"] = (
            invoicedata["saddrBnm"]
            + " "
            + invoicedata["saddrBno"]
            + " "
            + invoicedata["saddrFlno"]
            + " "
            + invoicedata["saddrSt"]
            + " "
            + invoicedata["saddrLoc"]
            + " "
            + invoicedata["saddrDist"]
            + "-"
            + invoicedata["saddrPncd"]
            + " "
            + invoicedata["saddrState"]
        )

        invoicedata1["sphno"] = invoicedata["sphno"] + ", " + invoicedata["sphno1"]

        temp = {
            "serialNumber": invoicedata.getlist("serialNumber"),
            "desc": invoicedata.getlist("desc"),
            "hsn_sac": invoicedata.getlist("hsn_sac"),
            "qty": invoicedata.getlist("qty"),
            "uom": invoicedata.getlist("uom"),
            "rate": invoicedata.getlist("rate"),
            "gst": invoicedata.getlist("gst"),
        }

        # Convert the strings to floats and round to 2 decimal places
        temp["qty"] = [round(float(item), 2) for item in temp["qty"]]
        temp["rate"] = [round(float(item), 2) for item in temp["rate"]]
        temp["gst"] = [round(float(item), 2) for item in temp["gst"]]

        temp["amount"] = []
        for i in range(len(temp["serialNumber"])):
            temp["amount"].append(round(temp["rate"][i] * temp["qty"][i], 2))

        invoicedata1["total-amount"] = round(sum(temp["amount"]), 2)
        invoicedata1["grand-total"] = round(invoicedata1["total-amount"])
        invoicedata1["round-off"] = round(
            invoicedata1["total-amount"] - invoicedata1["grand-total"]
        )

        temp["cgstrate"] = []
        temp["cgstamount"] = []
        temp["sgstrate"] = []
        temp["sgstamount"] = []
        temp["igstrate"] = []
        temp["igstamount"] = []
        total = {}
        total["qty"] = 0
        total["amount"] = 0
        total["cgstamount"] = 0
        total["sgstamount"] = 0
        total["igstamount"] = 0
        ograte = []
        # Calculate rate and amount in temp without gst
        for i in range(len(temp["serialNumber"])):
            ograte.append(temp["rate"][i])
            temp["rate"][i] = round(temp["rate"][i] * (1 - (temp["gst"][i] / 100)), 2)
            temp["amount"][i] = round(temp["rate"][i] * temp["qty"][i], 2)
            temp["cgstrate"].append(round(temp["gst"][i] / 2, 2))
            temp["cgstamount"].append(
                round((temp["cgstrate"][i] / 100) * temp["amount"][i], 2)
            )
            total["qty"] += temp["qty"][i]
            total["amount"] += temp["amount"][i]
            total["cgstamount"] += temp["cgstamount"][i]
            if company["addrState"] == invoicedata["baddrState"]:
                temp["sgstrate"].append(round(temp["gst"][i] / 2, 2))
                temp["sgstamount"].append(
                    round((temp["sgstrate"][i] / 100) * temp["amount"][i], 2)
                )
                temp["igstrate"].append("")
                temp["igstamount"].append("")
                total["sgstamount"] += temp["sgstamount"][i]
            else:
                temp["igstrate"].append(round(temp["gst"][i], 2))
                temp["igstamount"].append(
                    round((temp["igstrate"][i] / 100) * temp["amount"][i], 2)
                )
                temp["sgstrate"].append("")
                temp["sgstamount"].append("")
                total["igstamount"] += temp["igstamount"][i]

        invoicedata1["amountwords"] = (
            num2words(
                invoicedata1["total-amount"],
                lang="en_IN",
                to="currency",
                currency="INR",
            ).title()
            + " Only"
        )

        # Convert temp from dict of list to list of dict as items
        # items = [
        #     {key: value[i] for key, value in temp.items()}
        #     for i in range(len(temp["serialNumber"]))
        # ]
        items = [dict(zip(temp, values)) for values in zip(*temp.values())]

        rendered_template = render_template(
            "cl_invoice_template_custom.html",
            company=company,
            invoicedata=invoicedata,
            invoicedata1=invoicedata1,
            items=items,
            invoice_num=invoice_num_formatted,
            invoice_date=IN_format,
            total=total,
        )

        # Configure pdfkit options
        pdf_options = {
            "page-size": "A4",
            # "margin-top": "0mm",
            # "margin-right": "0mm",
            # "margin-bottom": "0mm",
            # "margin-left": "0mm",
            "encoding": "UTF-8",
            # # "no-outline": None,
        }

        # send response to browser as pdf
        pdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

        # When new beneficiary is added, add that to beneficiaries table in database
        if (
            invoicedata["billed_to"] == invoicedata["shipped_to"]
            and invoicedata["baddrBno"] == invoicedata["saddrBno"]
        ):
            ben_inv_id = db.execute(
                "SELECT id FROM beneficiaries WHERE name = ? AND company_id = ?",
                invoicedata["billed_to"],
                session["company_id"],
            )

            try:
                ben_inv_id = ben_inv_id[0]["id"]
            except:
                ben_inv_id = db.execute(
                    "INSERT INTO beneficiaries (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, type, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    invoicedata["billed_to"],
                    invoicedata["baddrBnm"],
                    invoicedata["baddrBno"],
                    invoicedata["baddrFlno"],
                    invoicedata["baddrSt"],
                    invoicedata["baddrLoc"],
                    invoicedata["baddrDist"],
                    invoicedata["baddrState"],
                    invoicedata["baddrPncd"],
                    invoicedata["bphno"],
                    invoicedata["bphno1"],
                    invoicedata["bgstin"],
                    "billed",
                    session["company_id"],
                    session["user_id"],
                )
            ben_ship_id = ben_inv_id

        else:
            ben_inv_id = db.execute(
                "SELECT id FROM beneficiaries WHERE name = ? AND addrBnm = ? AND company_id = ?",
                invoicedata["billed_to"],
                invoicedata["baddrBnm"],
                session["company_id"],
            )

            try:
                ben_inv_id = ben_inv_id[0]["id"]
            except:
                ben_inv_id = db.execute(
                    "INSERT INTO beneficiaries (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, type, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    invoicedata["billed_to"],
                    invoicedata["baddrBnm"],
                    invoicedata["baddrBno"],
                    invoicedata["baddrFlno"],
                    invoicedata["baddrSt"],
                    invoicedata["baddrLoc"],
                    invoicedata["baddrDist"],
                    invoicedata["baddrState"],
                    invoicedata["baddrPncd"],
                    invoicedata["bphno"],
                    invoicedata["bphno1"],
                    invoicedata["bgstin"],
                    "invoiced",
                    session["company_id"],
                    session["user_id"],
                )

            ben_ship_id = db.execute(
                "SELECT id FROM beneficiaries WHERE name = ? and addrBnm = ? AND company_id = ?",
                invoicedata["shipped_to"],
                invoicedata["saddrBnm"],
                session["company_id"],
            )

            try:
                ben_ship_id = ben_ship_id[0]["id"]
            except:
                ben_ship_id = db.execute(
                    "INSERT INTO beneficiaries (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, type, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    invoicedata["shipped_to"],
                    invoicedata["saddrBnm"],
                    invoicedata["saddrBno"],
                    invoicedata["saddrFlno"],
                    invoicedata["saddrSt"],
                    invoicedata["saddrLoc"],
                    invoicedata["saddrDist"],
                    invoicedata["saddrState"],
                    invoicedata["saddrPncd"],
                    invoicedata["sphno"],
                    invoicedata["sphno1"],
                    invoicedata1["sgstin"],
                    "shipped",
                    session["company_id"],
                    session["user_id"],
                )

        # Store history in database
        history_id = db.execute(
            "INSERT INTO history (bill_num, type, billed_to, shipped_to, transport, payment, eta, amount, pdf, company_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            invoice_num_db,
            "Invoice",
            ben_inv_id,
            ben_ship_id,
            invoicedata["transport-mode"],
            invoicedata["payment-mode"],
            invoicedata["eta"],
            invoicedata1["grand-total"],
            pdf,
            session["company_id"],
            session["user_id"],
        )

        if not history_id:
            return apology("Something went wrong", 500)

        # When new items are added, add that to goods table in database
        for i in range(len(items)):
            dbitemid = db.execute(
                "SELECT id FROM goods WHERE desc = ? AND company_id = ?",
                items[i]["desc"],
                session["company_id"],
            )

            try:
                dbitemid = dbitemid[0]["id"]
            except:
                dbitemid = db.execute(
                    "INSERT INTO goods (desc, hsn_sac, uom, rate, gst, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    items[i]["desc"],
                    items[i]["hsn_sac"],
                    items[i]["uom"],
                    ograte[i],
                    items[i]["gst"],
                    session["company_id"],
                    session["user_id"],
                )

            db.execute(
                "INSERT INTO history_goods (history_id, goods_id, qty) VALUES (?, ?, ?)",
                history_id,
                dbitemid,
                items[i]["qty"],
            )

        # return invoice as pdf
        # response = make_response(pdf)
        # response.headers["Content-Type"] = "application/pdf"
        # response.headers[
        #     "Content-Disposition"
        # ] = f"inline; filename={invoice_num_formatted}.pdf"
        # return response
        return send_file(
            io.BytesIO(pdf),
            mimetype="application/pdf",
            download_name=f"{invoice_num_formatted}.pdf",
            as_attachment=True,
        )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "invoice.html",
            invoice_num=invoice_num_formatted,
            invoice_date=IN_format,
            invoicenav=activepage,
        )


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Generate a quotation and send it to the user"""

    # Get the last quotation number which is in the format of financial years-month-six digit number
    quote_num = db.execute(
        "SELECT bill_num FROM history WHERE company_id = ? and type = ? ORDER BY id DESC LIMIT 1",
        session["company_id"],
        "Quotation",
    )

    # Reset the quotation number every year on the 1st of April
    current_date = datetime.date.today()

    if len(quote_num) == 0:
        quote_num = 1
        if current_date.month < 4:
            year = current_date.year - 1
        else:
            year = current_date.year

    else:
        if current_date.month < 4:
            year = current_date.year - 1
            quote_num = int(quote_num[0]["bill_num"][-6:]) + 1

        else:
            year = current_date.year
            if quote_num[0]["bill_num"][3:5] == str(current_date.year):
                quote_num = 1
            else:
                quote_num = int(quote_num[0]["bill_num"][-6:]) + 1

    quote_num_db = f"{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(quote_num).zfill(6)}"
    quote_num_formatted = f"EST-{quote_num_db}"
    IN_format = current_date.strftime("%d/%m/%Y")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        quotedata = request.form
        # print(quotedata)

        company = db.execute(
            "SELECT * FROM companies WHERE id = ?", session["company_id"]
        )
        company = company[0]
        company["addr"] = (
            company["addrBnm"]
            + " "
            + company["addrBno"]
            + " "
            + company["addrFlno"]
            + " "
            + company["addrSt"]
            + " "
            + company["addrLoc"]
            + " "
            + company["addrDist"]
            + "-"
            + company["addrPncd"]
            + " "
            + company["addrState"]
        )
        company["phno"] = company["phno1"] + ", " + company["phno2"]

        temp = {
            "serialNumber": quotedata.getlist("serialNumber"),
            "desc": quotedata.getlist("desc"),
            "hsn_sac": quotedata.getlist("hsn_sac"),
            "qty": quotedata.getlist("qty"),
            "uom": quotedata.getlist("uom"),
            "rate": quotedata.getlist("rate"),
            "gst": quotedata.getlist("gst"),
        }

        # Convert the strings to floats and round to 2 decimal places
        temp["qty"] = [round(float(item), 2) for item in temp["qty"]]
        temp["rate"] = [round(float(item), 2) for item in temp["rate"]]
        temp["gst"] = [round(float(item), 2) for item in temp["gst"]]

        temp["amount"] = []
        for i in range(len(temp["serialNumber"])):
            temp["amount"].append(round(temp["rate"][i] * temp["qty"][i], 2))

        quotedata1 = {}

        quotedata1["total-amount"] = round(sum(temp["amount"]), 2)
        quotedata1["grand-total"] = round(quotedata1["total-amount"])
        quotedata1["round-off"] = round(
            quotedata1["total-amount"] - quotedata1["grand-total"]
        )

        temp["cgstrate"] = []
        temp["cgstamount"] = []
        temp["sgstrate"] = []
        temp["sgstamount"] = []
        total = {}
        total["qty"] = 0
        total["amount"] = 0
        total["cgstamount"] = 0
        total["sgstamount"] = 0
        ograte = []
        # Calculate rate and amount in temp without gst
        for i in range(len(temp["serialNumber"])):
            ograte.append(temp["rate"][i])
            temp["rate"][i] = round(temp["rate"][i] * (1 - (temp["gst"][i] / 100)), 2)
            temp["amount"][i] = round(temp["rate"][i] * temp["qty"][i], 2)
            temp["cgstrate"].append(round(temp["gst"][i] / 2, 2))
            temp["cgstamount"].append(
                round((temp["cgstrate"][i] / 100) * temp["amount"][i], 2)
            )
            total["qty"] += temp["qty"][i]
            total["amount"] += temp["amount"][i]
            total["cgstamount"] += temp["cgstamount"][i]
            temp["sgstrate"].append(round(temp["gst"][i] / 2, 2))
            temp["sgstamount"].append(
                round((temp["sgstrate"][i] / 100) * temp["amount"][i], 2)
            )
            total["sgstamount"] += temp["sgstamount"][i]

        quotedata1["amountwords"] = (
            num2words(
                quotedata1["total-amount"],
                lang="en_IN",
                to="currency",
                currency="INR",
            ).title()
            + " Only"
        )

        items = [dict(zip(temp, values)) for values in zip(*temp.values())]

        rendered_template = render_template(
            "cl_quote_template_custom.html",
            company=company,
            quotedata=quotedata,
            quotedata1=quotedata1,
            items=items,
            quote_num=quote_num_formatted,
            quote_date=IN_format,
            total=total,
        )

        # Configure pdfkit options
        pdf_options = {
            "page-size": "A4",
            # "margin-top": "0mm",
            # "margin-right": "0mm",
            # "margin-bottom": "0mm",
            # "margin-left": "0mm",
            "encoding": "UTF-8",
            # # "no-outline": None,
        }

        # send response to browser as pdf
        quotepdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

        # When new beneficiary is added, add that to beneficiaries table in database
        ben_est_id = db.execute(
            "SELECT id FROM beneficiaries WHERE name = ? AND company_id = ?",
            quotedata["quoted_to"],
            session["company_id"],
        )

        try:
            ben_est_id = ben_est_id[0]["id"]
        except:
            ben_est_id = db.execute(
                "INSERT INTO beneficiaries (name, phno1, type, company_id, added_by) VALUES (?, ?, ?, ?, ?)",
                quotedata["quoted_to"],
                quotedata["phno"],
                "quoted",
                session["company_id"],
                session["user_id"],
            )
            # print(ben_est_id)

        # Store history in database
        history_id = db.execute(
            "INSERT INTO history (bill_num, type, billed_to, eta, amount, pdf, company_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            quote_num_db,
            "Quotation",
            ben_est_id,
            quotedata["eta"],
            quotedata1["grand-total"],
            quotepdf,
            session["company_id"],
            session["user_id"],
        )

        if not history_id:
            return apology("Something went wrong", 500)

        # When new goods is added, add that to goods table in database
        for i in range(len(items)):
            dbitemid = db.execute(
                "SELECT id FROM goods WHERE desc = ? AND company_id = ?",
                items[i]["desc"],
                session["company_id"],
            )

            try:
                dbitemid = dbitemid[0]["id"]
            except:
                dbitemid = db.execute(
                    "INSERT INTO goods (desc, hsn_sac, uom, rate, gst, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    items[i]["desc"],
                    items[i]["hsn_sac"],
                    items[i]["uom"],
                    ograte[i],
                    items[i]["gst"],
                    session["company_id"],
                    session["user_id"],
                )

            db.execute(
                "INSERT INTO history_goods (history_id, goods_id, qty) VALUES (?, ?, ?)",
                history_id,
                dbitemid,
                items[i]["qty"],
            )

        # send quote as pdf
        # import io
        return send_file(
            io.BytesIO(quotepdf),
            mimetype="application/pdf",
            download_name=f"{quote_num_formatted}.pdf",
            as_attachment=True,
        )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "quote.html",
            quote_num=quote_num_formatted,
            quote_date=IN_format,
            quotenav=activepage,
        )


@app.route("/inventory")
@login_required
def inventory():
    """Show Inventory of goods and beneficiaries of the company"""

    clients_list = db.execute(
        "SELECT name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, added_at, added_by FROM beneficiaries WHERE company_id = ?",
        session["company_id"],
    )
    # print(clients_list)
    for client in clients_list:
        client["addr"] = (
            client["addrBnm"]
            + " "
            + client["addrBno"]
            + " "
            + client["addrFlno"]
            + " "
            + client["addrSt"]
            + " "
            + client["addrLoc"]
            + " "
            + client["addrDist"]
            + "-"
            + client["addrPncd"]
            + " "
            + client["addrState"]
        )

        client["phno"] = client["phno1"] + ", " + client["phno2"]
        added_by = db.execute(
            "SELECT username FROM users WHERE id = ?", client["added_by"]
        )

        client["added_by"] = added_by[0]["username"]

        goods_list = db.execute(
            "SELECT desc, hsn_sac, uom, rate, gst, added_at, added_by FROM goods WHERE company_id = ?",
            session["company_id"],
        )
        for good in goods_list:
            added_by = db.execute(
                "SELECT username FROM users WHERE id = ?", good["added_by"]
            )

            good["added_by"] = added_by[0]["username"]

    return render_template(
        "inventory.html",
        clients_list=clients_list,
        goods_list=goods_list,
        inventorynav=activepage,
    )


@app.route("/history")
@login_required
def history():
    """Show billing history of the company"""
    query = """
    SELECT
        h.id,
        CASE
            WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
            ELSE 'EST-' || h.bill_num
        END AS bill_num,
        h.bill_timestamp,
        h.type,
        COALESCE(b1.name, '') AS billed_to,
        COALESCE(b2.name, '') AS shipped_to,
        h.transport,
        h.payment,
        h.eta,
        h.amount,
        json_group_array (
            json_object (
                'descp',
                g.descp,
                'hsn_sac',
                g.hsn_sac,
                'uom',
                g.uom,
                'rate',
                g.rate,
                'gst',
                g.gst,
                'qty',
                hg.qty
            )
        ) AS list_of_goods
    FROM
        history AS h
        LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
        LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
        LEFT JOIN history_goods AS hg ON h.id = hg.history_id
        LEFT JOIN goods AS g ON hg.goods_id = g.id
    WHERE
        h.company_id = ?
    GROUP BY
        h.id,
        h.bill_num,
        h.bill_timestamp,
        h.type,
        billed_to,
        shipped_to,
        h.transport,
        h.payment,
        h.eta,
        h.amount
    ORDER BY
        h.id DESC;
    """

    history_list = db.execute(query, session["company_id"])

    invoice_list = []
    quotation_list = []

    for history in history_list:
        history["list_of_goods"] = json.loads(history["list_of_goods"])
        if history["type"] == "Invoice":
            invoice_list.append(history)
        else:
            quotation_list.append(history)

    return render_template(
        "history.html",
        invoice_list=invoice_list,
        quotation_list=quotation_list,
        historynav=activepage,
    )


@app.route("/settings")
@login_required
def settings():
    """Show settings options"""
    company = db.execute(
        "SELECT custTerms FROM companies WHERE id = ?", session["company_id"]
    )
    # print(company[0])
    return render_template("settings.html", company=company[0], settingsnav=activepage)


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

        # # Ensure email was submitted
        # regemail = request.form.get("email")
        # if not regemail:
        #     return apology("must provide Email Address")

        # Ensure password was submitted
        regpassword = request.form.get("password")
        if not regpassword:
            return apology("must provide password")

        # Ensure confirmation was submitted
        regconfirm = request.form.get("confirmpassword")
        if not regconfirm:
            return apology("must provide password (again)")

        if not regpassword == regconfirm:
            return apology("password must be same")

        regid = db.execute(
            "INSERT INTO users (username, email, hash, phno, type) VALUES(?, ?, ?, ?, ?)",
            regusername,
            request.form.get("email"),
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
        flash(
            "This page is only for Admins who wants to register themselves as well as their company. This page will be followed by a company registration form. For user registration, please contact your company admin. Thank you!"
        )
        return render_template("register.html", registernav=activepage)


@app.route("/compregister", methods=["GET", "POST"])
def compregister():
    """Register company"""

    # Fetch default customer terms
    defaults = db.execute("SELECT custTerms FROM defaults")
    defaults = defaults[0]

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
        compreg["addrFlno"] = request.form.get("addrFlno")
        compreg["phno2"] = request.form.get("phno2")
        compreg["email"] = request.form.get("email")
        compreg["website"] = request.form.get("website")
        compreg["bnkAcnm"] = request.form.get("bnkAcnm")
        compreg["bnkAcno"] = request.form.get("bnkAcno")
        compreg["bnkNm"] = request.form.get("bnkNm")
        compreg["bnkIfsc"] = request.form.get("bnkIfsc")
        compreg["custTerms"] = request.form.get("custTerms")

        # UNIQUE fields
        # Validate mobile number and check if it exists
        # Check for a valid mobile number
        valid = validate_phno(compreg["phno1"])
        if not valid:
            return apology("Invalid mobile number")

        # Query database for phno1
        compregphno1 = db.execute(
            "SELECT * FROM companies WHERE phno1 = ?", compreg["phno1"]
        )

        # Check phno1 exists
        if len(compregphno1) == 1:
            return apology("Phone number already registered")

        # Validate email address and check if it exists
        # Check for a valid email address
        valid = validate_email(compreg["email"])
        if not valid:
            return apology("Invalid email address")

        # Query database for email
        compregemail = db.execute(
            "SELECT * FROM companies WHERE email = ?", compreg["email"]
        )

        # Check email exists
        if len(compregemail) == 1:
            return apology("Email already registered")

        # Check if GSTIN already exists
        # Query database for gstin
        compreggstin = db.execute(
            "SELECT * FROM companies WHERE gstin = ?", compreg["gstin"]
        )

        # Check gstin exists
        if len(compreggstin) == 1:
            return apology("GSTIN already registered")

        # Check if Bank account number already exists
        # Query database for bank account number
        compregbnkAcno = db.execute(
            "SELECT * FROM companies WHERE bnkAcno = ?", compreg["bnkAcno"]
        )

        # Check bank account number exists
        if len(compregbnkAcno) == 1:
            return apology("Bank account number already registered")

        # Done until here

        regcompid = db.execute(
            "INSERT INTO companies (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, email, website, gstin, bnkAcnm, bnkAcno, bnkNm, bnkIfsc, custTerms) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            compreg["name"],
            compreg["addrBnm"],
            compreg["addrBno"],
            compreg["addrFlno"],
            compreg["addrSt"],
            compreg["addrLoc"],
            compreg["addrDist"],
            compreg["addrState"],
            compreg["addrPncd"],
            compreg["phno1"],
            compreg["phno2"],
            compreg["email"],
            compreg["website"],
            compreg["gstin"],
            compreg["bnkAcnm"],
            compreg["bnkAcno"],
            compreg["bnkNm"],
            compreg["bnkIfsc"],
            compreg["custTerms"],
        )

        # Check if company is registered
        if not regcompid:
            return apology("Something went wrong")

        # Remember which company is user related to
        session["company_id"] = regcompid

        # Update user with company id
        regcompuserupdate = db.execute(
            "UPDATE users SET company_id = ? WHERE id = ?",
            regcompid,
            session["user_id"],
        )

        # Check if user is updated with company_id
        if not regcompuserupdate:
            return apology("Something went wrong")

        # Redirect user to home page
        flash("Company is successfully registered")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # print(session)
        try:
            if session["company_id"]:
                flash("Company is already registered")
                return redirect("/")
        finally:
            return render_template(
                "compregister.html", registernav=activepage, defaults=defaults
            )


@app.route("/download_pdf/<int:pdf_id>")
def download_pdf(pdf_id):
    pdf_data = db.execute(
        "SELECT bill_num, type, pdf FROM history WHERE id=? AND company_id=?",
        pdf_id,
        session["company_id"],
    )

    if pdf_data:
        if pdf_data[0]["type"] == "Invoice":
            bill_num_formatted = "INV-" + pdf_data[0]["bill_num"]
        else:
            bill_num_formatted = "EST-" + pdf_data[0]["bill_num"]

        return send_file(
            io.BytesIO(pdf_data[0]["pdf"]),
            mimetype="application/pdf",
            download_name=f"{bill_num_formatted}.pdf",
            as_attachment=True,
        )

    else:
        return "PDF not found."


@app.route("/change_password", methods=["POST"])
def change_password():
    passwords = request.form

    if not passwords["old_password"]:
        return apology("Old password not provided")

    if not passwords["new_password"]:
        return apology("New password not provided")

    if not passwords["confirm_password"]:
        return apology("New password not confirmed")

    if passwords["new_password"] != passwords["confirm_password"]:
        return apology("New password does not match")

    user = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])

    if not check_password_hash(user[0]["hash"], passwords["old_password"]):
        return apology("Old password does not match")

    confirm = db.execute(
        "UPDATE users SET hash = ? WHERE id = ?",
        generate_password_hash(passwords["new_password"]),
        session["user_id"],
    )

    if not confirm:
        return apology("Something went wrong")
    else:
        flash("Password changed successfully")
        return redirect("/settings")


@app.route("/change_terms", methods=["POST"])
def change_terms():
    terms = request.form

    if not terms["new_terms"]:
        return apology("Terms and conditions not provided")

    confirm = db.execute(
        "UPDATE companies SET custTerms = ? WHERE id = ?",
        terms["new_terms"],
        session["company_id"],
    )

    if not confirm:
        return apology("Something went wrong")
    else:
        flash("Terms and conditions changed successfully")
        return redirect("/settings")
