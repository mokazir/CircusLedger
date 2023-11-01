import os
import io
import time

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Import date class from datetime module
import datetime, pdfkit

from num2words import num2words

from helpers import (
    apology,
    login_required,
    user_required,
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


@app.route("/")
@login_required
def index():
    """Show homepage"""
    query = """
    SELECT
        h.id,
        h.bill_num,
        h.bill_timestamp,
        h.type,
        b1.name AS billed_to,
        b2.name AS shipped_to,
        h.transport,
        h.payment,
        h.eta,
        h.amount,
        g.descp,
        g.hsn_sac,
        g.uom,
        g.rate,
        g.gst,
        hg.qty,
        hg.amount AS good_amount
    FROM
        (
            SELECT
                id
            FROM
                history
            WHERE
                company_id = ?
                AND type = ?
            ORDER BY
                id DESC
            LIMIT
                5
        ) AS distinct_ids
        JOIN history AS h ON distinct_ids.id = h.id
        LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
        LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
        LEFT JOIN history_goods AS hg ON h.id = hg.history_id
        LEFT JOIN goods AS g ON hg.goods_id = g.id;
    """

    try:
        invoice_data = db.execute(query, session["company_id"], "Invoice")
        quotation_data = db.execute(query, session["company_id"], "Quotation")
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: IND-HIST-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    invoice_list = []
    quotation_list = []
    current_history_id = None

    for history in invoice_data + quotation_data:
        if history["id"] != current_history_id:
            current_history_id = history["id"]
            entry = {
                "id": history["id"],
                "bill_num": bill_num_formatr(
                    history["type"], history["bill_timestamp"], history["bill_num"]
                ),
                "bill_timestamp": history["bill_timestamp"],
                "billed_to": history["billed_to"] or "",
                "shipped_to": history["shipped_to"] or "",
                "transport": history["transport"] or "",
                "payment": history["payment"] or "",
                "eta": history["eta"] or "",
                "amount": history["amount"],
                "list_of_goods": [],
            }

            if history["type"] == "Invoice":
                invoice_list.append(entry)
            else:
                quotation_list.append(entry)

        entry["list_of_goods"].append(
            {
                "descp": history["descp"],
                "hsn_sac": history["hsn_sac"] or "",
                "uom": history["uom"] or "",
                "rate": history["rate"],
                "gst": history["gst"],
                "qty": history["qty"],
                "amount": history["good_amount"],
            }
        )

    return render_template(
        "index.html",
        invoice_list=invoice_list,
        quotation_list=quotation_list,
        homenav=activepage,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        login_data = request.form

        required_fields = ("username", "password")
        missing_fields = [
            field for field in required_fields if not login_data.get(field)
        ]
        if missing_fields:
            return apology(f"{', '.join(missing_fields)} not provided", 403)

        try:
            logged_user_db = db.execute(
                "SELECT * FROM users WHERE username = ?", login_data["username"]
            )
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: LOG-USR-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        if not logged_user_db:
            return apology("Invalid username", 400)
        if not check_password_hash(logged_user_db[0]["hash"], login_data["password"]):
            return apology("Invalid password", 400)

        session["user_id"] = logged_user_db[0]["id"]
        session["company_id"] = logged_user_db[0]["company_id"]

        return redirect("/")
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

    # Get the last invoice number
    try:
        invoice_num_db = db.execute(
            "SELECT bill_num, bill_timestamp FROM history WHERE company_id = ? AND type = ? ORDER BY id DESC LIMIT 1",
            session["company_id"],
            "Invoice",
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: INV-NUM-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Reset the invoice number every financial year on the 1st of April
    current_date = datetime.date.today()

    if not invoice_num_db:
        invoice_num = 1
        if current_date.month < 4:
            year = current_date.year - 1
        else:
            year = current_date.year

    else:
        invoice_num_db = invoice_num_db[0]
        if current_date.month < 4:
            year = current_date.year - 1
            invoice_num = invoice_num_db["bill_num"] + 1

        else:
            year = current_date.year
            if int(invoice_num_db["bill_timestamp"][5:7]) < 4:
                invoice_num = 1
            else:
                invoice_num = invoice_num_db["bill_num"] + 1

    invoice_num_formatted = f"INV-{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(invoice_num).zfill(6)}"
    IN_format = current_date.strftime("%d-%m-%Y")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        invoice_data = request.form

        clients_billing_fields = (
            "bname",
            "bphno1",
            "bphno2",
            "bgstin",
            "baddrBnm",
            "baddrBno",
            "baddrFlno",
            "baddrSt",
            "baddrLoc",
            "baddrDist",
            "baddrState",
            "baddrPncd",
        )
        clients_shipping_fields = (
            "sname",
            "sphno1",
            "sphno2",
            "sgstin",
            "saddrBnm",
            "saddrBno",
            "saddrFlno",
            "saddrSt",
            "saddrLoc",
            "saddrDist",
            "saddrState",
            "saddrPncd",
        )
        goods_fields = (
            "serialNumber",
            "descp",
            "hsn_sac",
            "qty",
            "uom",
            "rate",
            "amount",
            "gst",
        )
        info_fields = (
            "transport-mode",
            "payment-mode",
            "eta",
        )
        other_fields = ("total-amount",)
        missing_fields = [
            field
            for field in clients_billing_fields
            + clients_shipping_fields
            + goods_fields
            + info_fields
            + other_fields
            if invoice_data.get(field) is None
        ]
        if missing_fields:
            message = f"{', '.join(missing_fields)} not provided"
            return render_template("message.html", message=message), 403

        goods_data = {
            field: [value.strip() for value in invoice_data.getlist(field)]
            for field in goods_fields
        }

        required_goods_fields = {"descp": "", "qty": 0.001, "rate": 0.01, "gst": 0}
        missing_required_goods_fields = [
            key for key in required_goods_fields.keys() if not all(goods_data[key])
        ]
        if missing_required_goods_fields:
            message = f"{', '.join(missing_required_goods_fields)} not provided"
            return render_template("message.html", message=message), 403

        required_goods_fields.pop("descp")

        try:
            goods_data.update(
                {
                    key: [
                        float(value)
                        for value in goods_data[key]
                        if float(value) >= min_value
                    ]
                    for key, min_value in required_goods_fields.items()
                }
            )
        except:
            message = f"Invalid values in {' or '.join(required_goods_fields.keys())}"
            return render_template("message.html", message=message), 403

        goods_data_length = {len(values) for values in goods_data.values()}
        if len(goods_data_length) != 1:
            message = f"All fields in the list of goods must have the same length and {', '.join(required_goods_fields.keys())} fields must be higher than their minimum values"
            return render_template("message.html", message=message), 403

        clients_data = {
            field: invoice_data[field].strip()
            for field in clients_billing_fields + clients_shipping_fields + info_fields
        }

        pncd_fields = ("baddrPncd", "saddrPncd")
        if any(
            not is_valid_pncd(clients_data[field])
            for field in pncd_fields
            if clients_data[field]
        ):
            message = "Invalid Pincode"
            return render_template("message.html", message=message), 403

        phno_fields = ("phno1", "phno2")
        phno_fields_with_b = [f"b{field}" for field in phno_fields]
        phno_fields_with_s = [f"s{field}" for field in phno_fields]
        if any(
            not is_valid_phno(clients_data[field])
            for field in phno_fields_with_b + phno_fields_with_s
            if clients_data[field]
        ):
            message = "Invalid Phone Number"
            return render_template("message.html", message=message), 403

        # Dummy data for db insert on benificiary """need to CHANGE"""
        clients_data["sgstin"] = ""
        #############

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
        address_fields_with_b = [f"b{field}" for field in address_fields]
        clients_data["baddr"] = " ".join(
            clients_data[field]
            for field in address_fields_with_b
            if clients_data[field]
        )
        clients_data["bphno"] = ", ".join(
            clients_data[field] for field in phno_fields_with_b if clients_data[field]
        )

        address_fields_with_s = [f"s{field}" for field in address_fields]
        clients_data["saddr"] = " ".join(
            clients_data[field]
            for field in address_fields_with_s
            if clients_data[field]
        )
        clients_data["sphno"] = ", ".join(
            clients_data[field] for field in phno_fields_with_s if clients_data[field]
        )
        if clients_data["eta"]:
            try:
                clients_data["eta"] = datetime.datetime.strptime(
                    clients_data["eta"], "%Y-%m-%d"
                ).strftime("%d-%m-%Y")
            except:
                message = f"Invalid values in ETA"
                return render_template("message.html", message=message), 403

        goods_data["amount"] = [
            rate * qty for rate, qty in zip(goods_data["rate"], goods_data["qty"])
        ]

        genratd_data = {}
        genratd_data["total_qty"] = round(sum(goods_data["qty"]), 3)
        genratd_data["total_amount"] = round(sum(goods_data["amount"]), 2)
        genratd_data["grand_total"] = round(genratd_data["total_amount"])
        genratd_data["round_off"] = round(
            genratd_data["grand_total"] - genratd_data["total_amount"], 2
        )
        genratd_data[
            "total_amount_words"
        ] = f"{num2words(float(genratd_data['grand_total']), lang='en_IN', to='currency', currency='INR').title()} Only"

        goods_data["rate_wo_gst"] = [
            round(rate * (1 - gst / 100), 2)
            for rate, gst in zip(goods_data["rate"], goods_data["gst"])
        ]
        goods_data["amount_wo_gst"] = [
            round(rate * qty, 2)
            for rate, qty in zip(goods_data["rate_wo_gst"], goods_data["qty"])
        ]
        genratd_data["total_amount_wo_gst"] = round(sum(goods_data["amount_wo_gst"]), 2)

        try:
            company_db = db.execute(
                "SELECT * FROM companies WHERE id = ?", session["company_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-COMP-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        company_db = company_db[0]
        company_db["addr"] = " ".join(
            company_db[field] for field in address_fields if company_db[field]
        )
        company_db["phno"] = ", ".join(
            company_db[field] for field in phno_fields if company_db[field]
        )

        if company_db["addrState"] != clients_data["baddrState"]:
            goods_data["gst_amount"] = [
                round((gst_percent / 100) * amount, 2)
                for gst_percent, amount in zip(goods_data["gst"], goods_data["amount"])
            ]
            genratd_data["total_gst_amount"] = round(sum(goods_data["gst_amount"]), 2)
        else:
            goods_data["cgst_percent"] = [
                round(gst / 2, 2) for gst in goods_data["gst"]
            ]
            goods_data["cgst_amount"] = [
                round((cgst_percent / 100) * amount, 2)
                for cgst_percent, amount in zip(
                    goods_data["cgst_percent"], goods_data["amount"]
                )
            ]
            genratd_data["total_cgst_amount"] = round(sum(goods_data["cgst_amount"]), 2)
            goods_data["sgst_percent"] = goods_data["cgst_percent"]
            goods_data["sgst_amount"] = goods_data["cgst_amount"]
            genratd_data["total_sgst_amount"] = genratd_data["total_cgst_amount"]

        goods_data_list = [
            dict(zip(goods_data.keys(), values)) for values in zip(*goods_data.values())
        ]

        try:
            user_db = db.execute(
                "SELECT username, type FROM users WHERE id = ?", session["user_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-NAME-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        rendered_template = render_template(
            "cl_invoice_template.html",
            company=company_db,
            clients_data=clients_data,
            goods_data=goods_data_list,
            genratd_data=genratd_data,
            invoice_num=invoice_num_formatted,
            invoice_date=IN_format,
            user=user_db[0],
        )

        pdf_options = {
            "page-size": "A4",
            "encoding": "UTF-8",
        }

        pdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

        def get_or_insert_ben(select_query, select_params, insert_query, insert_params):
            try:
                ben_id_db = db.execute(select_query, *select_params)
                ben_id = (
                    ben_id_db[0]["id"]
                    if ben_id_db
                    else db.execute(insert_query, *insert_params)
                )
            except Exception as e:
                message = f"Something went wrong, please try again.\nError-code: INV-BEN-{type(e).__name__}.\nDEV-INFO: {e.args}"
                return render_template("message.html", message=message), 500

            return ben_id

        ben_select_query = "SELECT id FROM beneficiaries WHERE name = ? AND phno1 = ? AND company_id = ?"
        ben_select_inv_params = (
            clients_data["bname"],
            clients_data["bphno1"],
            session["company_id"],
        )
        ben_select_ship_params = (
            clients_data["sname"],
            clients_data["sphno1"],
            session["company_id"],
        )
        ben_insert_query = "INSERT INTO beneficiaries (name, phno1, phno2, gstin, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ben_insert_inv_params = (
            *(
                clients_data[field] if clients_data[field] else None
                for field in clients_billing_fields
            ),
            session["company_id"],
            session["user_id"],
        )
        ben_insert_ship_params = (
            *(
                clients_data[field] if clients_data[field] else None
                for field in clients_shipping_fields
            ),
            session["company_id"],
            session["user_id"],
        )

        ben_inv_id = None
        ben_ship_id = None
        if clients_data["bname"]:
            ben_inv_id = get_or_insert_ben(
                ben_select_query,
                ben_select_inv_params,
                ben_insert_query,
                ben_insert_inv_params,
            )

        if (
            clients_data["bname"] == clients_data["sname"]
            and clients_data["bphno1"] == clients_data["sphno1"]
        ):
            ben_ship_id = ben_inv_id

        elif clients_data["sname"]:
            ben_ship_id = get_or_insert_ben(
                ben_select_query,
                ben_select_ship_params,
                ben_insert_query,
                ben_insert_ship_params,
            )

        try:
            history_id = db.execute(
                "INSERT INTO history (bill_num, type, billed_to, shipped_to, transport, payment, eta, amount, pdf, company_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                invoice_num,
                "Invoice",
                ben_inv_id,
                ben_ship_id,
                *(clients_data[field] for field in info_fields),
                genratd_data["grand_total"],
                pdf,
                session["company_id"],
                session["user_id"],
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-HIST-INS-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        try:
            goods_data_db = db.execute(
                "SELECT id, descp FROM goods WHERE descp IN (?) AND company_id = ?",
                goods_data["descp"],
                session["company_id"],
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-GOODS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        if len(goods_data_db) not in goods_data_length:
            goods_in_db = {item["descp"] for item in goods_data_db}
            goods_to_add_list = [
                item for item in goods_data_list if item["descp"] not in goods_in_db
            ]
            for good in goods_to_add_list:
                try:
                    good_id = db.execute(
                        "INSERT INTO goods (descp, hsn_sac, uom, rate, gst, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        good["descp"],
                        good["hsn_sac"] if good["hsn_sac"] else None,
                        good["uom"] if good["uom"] else None,
                        good["rate"],
                        good["gst"],
                        session["company_id"],
                        session["user_id"],
                    )
                except Exception as e:
                    message = f"Something went wrong, please try again.\nError-code: INV-GOODS-INS-{type(e).__name__}.\nDEV-INFO: {e.args}"
                    return render_template("message.html", message=message), 500

                goods_data_db.append({"id": good_id, "descp": good["descp"]})

        id_mapping = {item["descp"]: item["id"] for item in goods_data_db}

        goods_data_list = [
            {**good, "id": id_mapping[good["descp"]]} for good in goods_data_list
        ]

        for good in goods_data_list:
            try:
                db.execute(
                    "INSERT INTO history_goods (history_id, goods_id, qty, amount) VALUES (?, ?, ?, ?)",
                    history_id,
                    good["id"],
                    good["qty"],
                    good["amount"],
                )
            except Exception as e:
                message = f"Something went wrong, please try again.\nError-code: INV-GOODS-LINK-{type(e).__name__}.\nDEV-INFO: {e.args}"
                return render_template("message.html", message=message), 500

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


@app.route("/quotation", methods=["GET", "POST"])
@login_required
def quotation():
    """Generate a quotation and send it to the user"""

    # Get the last quotation number
    try:
        quotation_num_db = db.execute(
            "SELECT bill_num, bill_timestamp FROM history WHERE company_id = ? and type = ? ORDER BY id DESC LIMIT 1",
            session["company_id"],
            "Quotation",
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: QUOT-NUM-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Reset the quotation number every year on the 1st of April
    current_date = datetime.date.today()

    if not quotation_num_db:
        quotation_num = 1
        if current_date.month < 4:
            year = current_date.year - 1
        else:
            year = current_date.year

    else:
        quotation_num_db = quotation_num_db[0]
        if current_date.month < 4:
            year = current_date.year - 1
            quotation_num = quotation_num_db["bill_num"] + 1

        else:
            year = current_date.year
            if int(quotation_num_db["bill_timestamp"][5:7]) < 4:
                quotation_num = 1
            else:
                quotation_num = quotation_num_db["bill_num"] + 1

    quotation_num_formatted = f"EST-{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(quotation_num).zfill(6)}"
    IN_format = current_date.strftime("%d/%m/%Y")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        quotation_data = request.form

        clients_fields = (
            "qname",
            "phno1",
        )
        goods_fields = (
            "serialNumber",
            "descp",
            "hsn_sac",
            "qty",
            "uom",
            "rate",
            "amount",
            "gst",
        )
        info_fields = ("eta",)
        other_fields = ("total-amount",)
        missing_fields = [
            field
            for field in clients_fields + goods_fields + info_fields + other_fields
            if quotation_data.get(field) is None
        ]
        if missing_fields:
            message = f"{', '.join(missing_fields)} not provided"
            return render_template("message.html", message=message), 403

        goods_data = {
            field: [value.strip() for value in quotation_data.getlist(field)]
            for field in goods_fields
        }

        required_goods_fields = {"descp": "", "qty": 0.001, "rate": 0.01, "gst": 0}
        missing_required_goods_fields = [
            key for key in required_goods_fields.keys() if not all(goods_data[key])
        ]
        if missing_required_goods_fields:
            message = f"{', '.join(missing_required_goods_fields)} not provided"
            return render_template("message.html", message=message), 403

        required_goods_fields.pop("descp")

        try:
            goods_data.update(
                {
                    key: [
                        float(value)
                        for value in goods_data[key]
                        if float(value) >= min_value
                    ]
                    for key, min_value in required_goods_fields.items()
                }
            )
        except Exception as e:
            message = f"Invalid values in {' or '.join(required_goods_fields.keys())}"
            return render_template("message.html", message=message), 403

        goods_data_length = {len(values) for values in goods_data.values()}
        if len(goods_data_length) != 1:
            message = f"All fields in the list of goods must have the same length and {', '.join(required_goods_fields.keys())} fields must be higher than their minimum values"
            return render_template("message.html", message=message), 403

        clients_data = {
            field: quotation_data[field].strip()
            for field in clients_fields + info_fields
        }

        if clients_data["phno1"]:
            if not is_valid_phno(clients_data["phno1"]):
                message = "Invalid mobile number"
                return render_template("message.html", message=message), 403
        if clients_data["eta"]:
            try:
                clients_data["eta"] = datetime.datetime.strptime(
                    clients_data["eta"], "%Y-%m-%d"
                ).strftime("%d-%m-%Y")
            except:
                message = f"Invalid values in ETA"
                return render_template("message.html", message=message), 403

        goods_data["amount"] = [
            rate * qty for rate, qty in zip(goods_data["rate"], goods_data["qty"])
        ]

        genratd_data = {}
        genratd_data["total_qty"] = round(sum(goods_data["qty"]), 3)
        genratd_data["total_amount"] = round(sum(goods_data["amount"]), 2)
        genratd_data["grand_total"] = round(genratd_data["total_amount"])
        genratd_data["round_off"] = round(
            genratd_data["grand_total"] - genratd_data["total_amount"], 2
        )
        genratd_data[
            "total_amount_words"
        ] = f"{num2words(float(genratd_data['grand_total']), lang='en_IN', to='currency', currency='INR').title()} Only"

        goods_data["rate_wo_gst"] = [
            round(rate * (1 - gst / 100), 2)
            for rate, gst in zip(goods_data["rate"], goods_data["gst"])
        ]
        goods_data["amount_wo_gst"] = [
            round(rate * qty, 2)
            for rate, qty in zip(goods_data["rate_wo_gst"], goods_data["qty"])
        ]

        goods_data["gst_amount"] = [
            round((gst_percent / 100) * amount, 2)
            for gst_percent, amount in zip(goods_data["gst"], goods_data["amount"])
        ]

        genratd_data["total_amount_wo_gst"] = round(sum(goods_data["amount_wo_gst"]), 2)
        genratd_data["total_gst_amount"] = round(sum(goods_data["gst_amount"]), 2)

        goods_data_list = [
            dict(zip(goods_data.keys(), values)) for values in zip(*goods_data.values())
        ]

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

        try:
            company_db = db.execute(
                "SELECT * FROM companies WHERE id = ?", session["company_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: QUOT-COMP-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        company_db = company_db[0]
        company_db["addr"] = " ".join(
            company_db[field] for field in address_fields if company_db[field]
        )
        company_db["phno"] = ", ".join(
            company_db[field] for field in ("phno1", "phno2") if company_db[field]
        )

        try:
            user_db = db.execute(
                "SELECT username, type FROM users WHERE id = ?", session["user_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: QUOT-NAME-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        rendered_template = render_template(
            "cl_quotation_template.html",
            company=company_db,
            clients_data=clients_data,
            goods_data=goods_data_list,
            genratd_data=genratd_data,
            quotation_num=quotation_num_formatted,
            quotation_date=IN_format,
            user=user_db[0],
        )

        pdf_options = {
            "page-size": "A4",
            "encoding": "UTF-8",
        }

        pdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

        def get_or_insert_ben(select_query, select_params, insert_query, insert_params):
            try:
                ben_id_db = db.execute(select_query, *select_params)
                ben_id = (
                    ben_id_db[0]["id"]
                    if ben_id_db
                    else db.execute(insert_query, *insert_params)
                )
            except Exception as e:
                message = f"Something went wrong, please try again.\nError-code: QUOT-BEN-INS-{type(e).__name__}.\nDEV-INFO: {e.args}"
                return render_template("message.html", message=message), 500

            return ben_id

        ben_select_query = "SELECT id FROM beneficiaries WHERE name = ? AND phno1 = ? AND company_id = ?"
        ben_select_params = (
            clients_data["qname"],
            clients_data["phno1"] if clients_data["phno1"] else None,
            session["company_id"],
        )
        ben_insert_query = "INSERT INTO beneficiaries (name, phno1, company_id, added_by) VALUES (?, ?, ?, ?)"
        ben_insert_params = (
            clients_data["qname"],
            clients_data["phno1"] if clients_data["phno1"] else None,
            session["company_id"],
            session["user_id"],
        )

        ben_est_id = None
        if clients_data["qname"]:
            ben_est_id = get_or_insert_ben(
                ben_select_query,
                ben_select_params,
                ben_insert_query,
                ben_insert_params,
            )

        try:
            history_id = db.execute(
                "INSERT INTO history (bill_num, type, billed_to, eta, amount, pdf, company_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                quotation_num,
                "Quotation",
                ben_est_id,
                clients_data["eta"],
                genratd_data["grand_total"],
                pdf,
                session["company_id"],
                session["user_id"],
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: QUOT-HIST-INS-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        try:
            goods_data_db = db.execute(
                "SELECT id, descp FROM goods WHERE descp IN (?) AND company_id = ?",
                goods_data["descp"],
                session["company_id"],
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: QUOT-GOODS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        if len(goods_data_db) not in goods_data_length:
            goods_in_db = {item["descp"] for item in goods_data_db}
            goods_to_add_list = [
                item for item in goods_data_list if item["descp"] not in goods_in_db
            ]
            for good in goods_to_add_list:
                try:
                    good_id = db.execute(
                        "INSERT INTO goods (descp, hsn_sac, uom, rate, gst, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        good["descp"],
                        good["hsn_sac"] if good["hsn_sac"] else None,
                        good["uom"] if good["uom"] else None,
                        good["rate"],
                        good["gst"],
                        session["company_id"],
                        session["user_id"],
                    )
                except Exception as e:
                    message = f"Something went wrong, please try again.\nError-code: QUOT-GOODS-INS-{type(e).__name__}.\nDEV-INFO: {e.args}"
                    return render_template("message.html", message=message), 500

                goods_data_db.append({"id": good_id, "descp": good["descp"]})

        id_mapping = {item["descp"]: item["id"] for item in goods_data_db}

        goods_data_list = [
            {**good, "id": id_mapping[good["descp"]]} for good in goods_data_list
        ]

        for good in goods_data_list:
            try:
                db.execute(
                    "INSERT INTO history_goods (history_id, goods_id, qty, amount) VALUES (?, ?, ?, ?)",
                    history_id,
                    good["id"],
                    good["qty"],
                    good["amount"],
                )
            except Exception as e:
                message = f"Something went wrong, please try again.\nError-code: QUOT-GOODS-LINK-{type(e).__name__}.\nDEV-INFO: {e.args}"
                return render_template("message.html", message=message), 500

        return send_file(
            io.BytesIO(pdf),
            mimetype="application/pdf",
            download_name=f"{quotation_num_formatted}.pdf",
            as_attachment=True,
        )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template(
            "quote.html",
            quote_num=quotation_num_formatted,
            quote_date=IN_format,
            quotenav=activepage,
        )


@app.route("/inventory")
@login_required
def inventory():
    """Show Inventory of goods and beneficiaries of the company"""
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
        good.update({k: good[k] or "" for k in optional_goods_fields})

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
        client.update({k: client[k] or "" for k in optional_clients_fields})

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
        h.bill_num,
        h.bill_timestamp,
        h.type,
        b1.name AS billed_to,
        b2.name AS shipped_to,
        h.transport,
        h.payment,
        h.eta,
        h.amount,
        g.descp,
        g.hsn_sac,
        g.uom,
        g.rate,
        g.gst,
        hg.qty,
        hg.amount AS good_amount
    FROM
        history AS h
        LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
        LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
        LEFT JOIN history_goods AS hg ON h.id = hg.history_id
        LEFT JOIN goods AS g ON hg.goods_id = g.id
    WHERE
        h.company_id = ?
    ORDER BY
        h.id DESC;
    """

    try:
        history_list = db.execute(query, session["company_id"])
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: HIST-BILL-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    invoice_list = []
    quotation_list = []
    current_history_id = None

    for history in history_list:
        if history["id"] != current_history_id:
            current_history_id = history["id"]
            entry = {
                "id": history["id"],
                "bill_num": bill_num_formatr(
                    history["type"], history["bill_timestamp"], history["bill_num"]
                ),
                "bill_timestamp": history["bill_timestamp"],
                "billed_to": history["billed_to"] or "",
                "shipped_to": history["shipped_to"] or "",
                "transport": history["transport"] or "",
                "payment": history["payment"] or "",
                "eta": history["eta"] or "",
                "amount": history["amount"],
                "list_of_goods": [],
            }

            if history["type"] == "Invoice":
                invoice_list.append(entry)
            else:
                quotation_list.append(entry)

        entry["list_of_goods"].append(
            {
                "descp": history["descp"],
                "hsn_sac": history["hsn_sac"] or "",
                "uom": history["uom"] or "",
                "rate": history["rate"],
                "gst": history["gst"],
                "qty": history["qty"],
                "amount": history["good_amount"],
            }
        )

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
    try:
        company_db = db.execute(
            "SELECT custTerms FROM companies WHERE id = ?", session["company_id"]
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: SET-TERMS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )
    return render_template(
        "settings.html", company=company_db[0], settingsnav=activepage
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()

    if request.method == "POST":
        register_data = request.form.to_dict()

        required_fields = ["username", "password", "confirm-password"]
        optional_fields = ["email", "phno"]

        missing_fields = [
            field
            for field in required_fields + optional_fields
            if register_data.get(field) is None
        ]
        if missing_fields:
            return apology(f"{', '.join(missing_fields)} not provided", 403)

        if len(register_data["username"]) < 5:
            return apology("Username must be at least 5 characters", 403)
        try:
            if db.execute(
                "SELECT id FROM users WHERE username = ?", register_data["username"]
            ):
                return apology("Username already exists", 409)
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: REG-NAME-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        if not is_valid_password(register_data["password"]):
            return apology(
                "Your password must be at least 8 characters long and include characters from at least two of the following categories: letters, numbers, special characters (including spaces), or even emojis.",
                403,
            )
        if register_data["password"] != register_data["confirm-password"]:
            return apology("Passwords must be same", 403)

        register_data.update(
            {
                field: None
                for field in optional_fields
                if not register_data[field].strip()
            }
        )

        if register_data["email"]:
            if not is_valid_email(register_data["email"]):
                return apology("Invalid email address", 400)
            try:
                if db.execute(
                    "SELECT id FROM users WHERE email = ?", register_data["email"]
                ):
                    return apology("Email already registered", 409)
            except Exception as e:
                return apology(
                    f"Something went wrong, please try again.\nError-code: REG-EMAIL-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                    500,
                )

        if register_data["phno"]:
            if not is_valid_phno(register_data["phno"]):
                return apology("Invalid phone number", 400)
            try:
                if db.execute(
                    "SELECT id FROM users WHERE phno = ?", register_data["phno"]
                ):
                    return apology("Phone number already registered", 409)
            except Exception as e:
                return apology(
                    f"Something went wrong, please try again.\nError-code: REG-PHNO-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                    500,
                )

        register_data["password"] = generate_password_hash(register_data["password"])
        required_fields.remove("confirm-password")
        try:
            reg_id_db = db.execute(
                "INSERT INTO users (username, hash, email, phno, type) VALUES(?, ?, ?, ?, ?)",
                *(register_data[field] for field in required_fields + optional_fields),
                "admin",
            )
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: REG-USR-INS-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        session["user_id"] = reg_id_db

        flash("User successfully registered")
        return redirect("/compregister")

    else:
        flash(
            "This page is only for Admins who wants to register themselves as well as their company. This page will be followed by a company registration form. For user registration, please contact your company admin. Thank you!"
        )
        return render_template("register.html", registernav=activepage)


@app.route("/compregister", methods=["GET", "POST"])
@user_required
def compregister():
    """Register company"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        compreg_data = request.form.to_dict()

        required_fields = (
            "company-name",
            "addrBno",
            "addrSt",
            "addrLoc",
            "addrDist",
            "addrState",
            "addrPncd",
            "phno1",
        )
        optional_fields = (
            "addrBnm",
            "addrFlno",
            "phno2",
            "email",
            "website",
            "gstin",
            "bnkAcnm",
            "bnkAcno",
            "bnkNm",
            "bnkIfsc",
            "custTerms",
        )

        missing_fields = [
            field
            for field in required_fields + optional_fields
            if compreg_data.get(field) is None
        ]
        if missing_fields:
            return apology(f"{', '.join(missing_fields)} not provided", 403)

        missing_required_fields = [
            field for field in required_fields if not compreg_data[field].strip()
        ]
        if missing_required_fields:
            return apology(f"{', '.join(missing_required_fields)} not provided", 403)

        if not is_valid_pncd(compreg_data["addrPncd"]):
            return apology("Invalid Pincode", 403)

        if not is_valid_phno(compreg_data["phno1"]):
            return apology("Invalid mobile number", 403)
        try:
            if db.execute(
                "SELECT id FROM companies WHERE phno1 = ?", compreg_data["phno1"]
            ):
                return apology("Mobile number already registered", 409)
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: COMPREG-PHNO-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        compreg_data.update(
            {
                field: None
                for field in optional_fields
                if not compreg_data[field].strip()
            }
        )

        if compreg_data["phno2"]:
            if not is_valid_phno(compreg_data["phno2"]):
                return apology("Invalid phone number", 400)

        if compreg_data["email"]:
            if not is_valid_email(compreg_data["email"]):
                return apology("Invalid email", 400)
            try:
                if db.execute(
                    "SELECT id FROM companies WHERE email = ?", compreg_data["email"]
                ):
                    return apology("Email already registered", 409)
            except Exception as e:
                return apology(
                    f"Something went wrong, please try again.\nError-code: COMPREG-EMAIL-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                    500,
                )

        if compreg_data["gstin"]:
            try:
                if db.execute(
                    "SELECT id FROM companies WHERE gstin = ?", compreg_data["gstin"]
                ):
                    return apology("GSTIN already registered", 409)
            except Exception as e:
                return apology(
                    f"Something went wrong, please try again.\nError-code: COMPREG-GSTIN-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                    500,
                )

        if compreg_data["bnkAcno"]:
            try:
                if db.execute(
                    "SELECT id FROM companies WHERE bnkAcno = ?",
                    compreg_data["bnkAcno"],
                ):
                    return apology("Bank account number already registered", 409)
            except Exception as e:
                return apology(
                    f"Something went wrong, please try again.\nError-code: COMPREG-BNKACNO-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                    500,
                )

        try:
            regcomp_id_db = db.execute(
                "INSERT INTO companies (name, addrBno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, addrBnm, addrFlno, phno2, email, website, gstin, bnkAcnm, bnkAcno, bnkNm, bnkIfsc, custTerms, created_by) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                *(compreg_data[field] for field in required_fields + optional_fields),
                session["user_id"],
            )
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: COMPREG-COMP-INS-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        try:
            db.execute(
                "UPDATE users SET company_id = ? WHERE id = ?",
                regcomp_id_db,
                session["user_id"],
            )
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: COMPREG-ID-UPD-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        session["company_id"] = regcomp_id_db

        flash("Company is successfully registered")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        if session.get("company_id"):
            flash("Company is already registered")
            return redirect("/")

        try:
            defaults_db = db.execute("SELECT custTerms FROM defaults")
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: COMPREG-DEF-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        return render_template(
            "compregister.html", registernav=activepage, defaults=defaults_db[0]
        )


@app.route("/download_pdf/<int:pdf_id>")
@login_required
def download_pdf(pdf_id):
    try:
        pdf_data = db.execute(
            "SELECT bill_num, bill_timestamp, type, pdf FROM history WHERE id = ? AND company_id = ?",
            pdf_id,
            session["company_id"],
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: DOWN-PDF-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    if pdf_data:
        pdf_data = pdf_data[0]
        bill_type = "Invoice" if pdf_data["type"] == "Invoice" else "Quotation"
        bill_num_formatted = bill_num_formatr(
            bill_type, pdf_data["bill_timestamp"], pdf_data["bill_num"]
        )

        return send_file(
            io.BytesIO(pdf_data["pdf"]),
            mimetype="application/pdf",
            download_name=f"{bill_num_formatted}.pdf",
            as_attachment=True,
        )

    else:
        return apology("PDF not found", 404)


@app.route("/change_password", methods=["POST"])
def change_password():
    passwords_data = request.form

    required_fields = ("current-password", "new-password", "confirm-password")
    missing_fields = [
        field for field in required_fields if not passwords_data.get(field)
    ]
    if missing_fields:
        return apology(f"{', '.join(missing_fields)} not provided", 403)

    if not is_valid_password(passwords_data["new-password"]):
        return apology(
            "Your password must be at least 8 characters long and include characters from at least two of the following categories: letters, numbers, special characters (including spaces), or even emojis.",
            403,
        )
    if passwords_data["new-password"] != passwords_data["confirm-password"]:
        return apology("New Password and Confirm Password must be same", 403)

    try:
        old_password_db = db.execute(
            "SELECT hash FROM users WHERE id = ?", session["user_id"]
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: CHNGPASS-PASS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    if not check_password_hash(
        old_password_db[0]["hash"], passwords_data["current-password"]
    ):
        return apology("Current Password does not match", 400)

    try:
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(passwords_data["new-password"]),
            session["user_id"],
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: CHNGPASS-PASS-UPD-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    flash("Password changed successfully")
    return redirect("/settings")


@app.route("/change_terms", methods=["POST"])
def change_terms():
    terms_data = request.form

    if not terms_data.get("new-terms"):
        return apology("New Terms and Conditions not provided", 403)

    try:
        db.execute(
            "UPDATE companies SET custTerms = ? WHERE id = ?",
            terms_data["new-terms"],
            session["company_id"],
        )
    except Exception as e:
        return apology(
            f"Something went wrong, please try again.\nError-code: CHNGTERMS-TERMS-UPD-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    flash("Terms and conditions changed successfully")
    return redirect("/settings")


import html


@app.route("/apology/<string:message>/<code>")
def apology(message, code):
    """Render message as an apology to user."""
    message = html.unescape(message)
    print(message)

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
