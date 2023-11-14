import datetime
import html
from io import BytesIO

import pdfkit
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, send_file, session
from num2words import num2words
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import (
    apology,
    bill_num_formatr,
    get_or_insert_ben,
    handle_error,
    inr,
    is_valid_email,
    is_valid_password,
    is_valid_phno,
    is_valid_pncd,
    login_required,
    user_required,
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
    """
    This function renders the home page.
    GET:
    - Retrieves invoice and quotation data from the database.
    - Renders the index.html template with the data.

    Parameters:
    - `GET` request:
        - None

    Returns:
    - `GET` request:
        - Rendered index.html template.

    Exception Handling:
    - If an exception occurs during the query execution, it is handled and an error message is returned.
    """

    # SQL query to retrieve invoice and quotation data
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
        # Retrieve the lastest 5 invoice and quotation data
        invoice_data = db.execute(query, session["company_id"], "Invoice")
        quotation_data = db.execute(query, session["company_id"], "Quotation")
    except Exception as e:
        # Return an error message if an exception occurs
        return apology(
            f"Something went wrong, please try again.\nError-code: IND-HIST-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Initialize lists to store invoice and quotation data
    invoice_list = []
    quotation_list = []
    current_history_id = None

    # Iterate over the invoice and quotation data
    for history in invoice_data + quotation_data:
        # Check if the current history entry is different from the previous one
        if history["id"] != current_history_id:
            # Update the current history ID
            current_history_id = history["id"]

            # Create a new dictionary entry for the history data
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

            # Append the entry to the appropriate list based on the history type
            if history["type"] == "Invoice":
                invoice_list.append(entry)
            else:
                quotation_list.append(entry)

        # Add the goods details to the list of goods for the current history entry
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

    # Render the index.html template with the invoice and quotation data
    return render_template(
        "index.html",
        invoice_list=invoice_list,
        quotation_list=quotation_list,
        homenav=activepage,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    This function handles the login process.
    It first clears the session.
    GET:
    - Renders the login template.
    POST:
    - Validates the login data.
    - Checks if the user exists and the password is correct.
    - If the user exists and the password is correct, it sets the session variables and redirects the user to the home page.
    - If the user does not exist or the password is incorrect, it returns an error message.

    Parameters:
    - `GET` request:
        - None
    - `POST` request:
        - `request.form`: Form data containing the username and password.

    Returns:
    - `GET` request:
        - Rendered login template.
    - `POST` request:
        - Redirects the user to the home page.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are returned in the response.
    """
    # Clear the session to ensure a clean state
    session.clear()

    if request.method == "POST":
        # If the request method is POST, process the login form
        # Retrieve the login data from the form
        login_data = request.form

        # Check if all required fields are provided
        required_fields = ("username", "password")
        missing_fields = [
            field for field in required_fields if not login_data.get(field)
        ]
        if missing_fields:
            # Return an error message if any required field is missing
            return apology(f"{', '.join(missing_fields)} not provided", 403)

        try:
            # Retrieve the user from the database based on the provided username
            logged_user_db = db.execute(
                "SELECT * FROM users WHERE username = ?", login_data["username"]
            )
        except Exception as e:
            # Return an error message if there is an exception while retrieving the user
            return apology(
                f"Something went wrong, please try again.\nError-code: LOG-USR-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        if not logged_user_db:
            # Return an error message if the username is invalid
            return apology("Invalid username", 400)
        if not check_password_hash(logged_user_db[0]["hash"], login_data["password"]):
            # Return an error message if the password is invalid
            return apology("Invalid password", 400)

        # Set the user ID and company ID in the session
        session["user_id"] = logged_user_db[0]["id"]
        session["company_id"] = logged_user_db[0]["company_id"]

        # Redirect the user to the home page
        return redirect("/")
    else:
        # If the request method is GET, render the login template
        return render_template("login.html", loginnav=activepage)


@app.route("/logout")
def logout():
    """
    This function handles the logout functionality.
    GET:
        It clears the session and redirects the user to the login page.

    Parameters:
    - `GET` request:
        - None

    Returns:
    - `GET` request:
        - Redirects the user to the login page.
    """
    # Clear the session data
    session.clear()

    # Redirect the user to the home page
    return redirect("/login")


@app.route("/invoice", methods=["GET", "POST"])
@login_required
def invoice():
    """
    This function handles the generation of invoices.
    GET:
    - Retrieves the last used invoice number from the database and calculates the next invoice number.
    - Renders invoice template for creating a new invoice with the calculated invoice number.
    POST:
    - Handles the form submission, validates the input data, and generates a PDF invoice.
    - It validates client and goods data, calculates various totals and taxes, and inserts the invoice and related information into the database.
    - Renders an HTML response containing the generated PDF for download.

    Parameters:
    - `GET` request:
        - None

    - `POST` request:
        - `request.form`: Form data containing client information, goods details, and other invoice-related data.

    Returns:
    - `GET` request:
        - Rendered invoice template.

    - `POST` request:
        - Returns a downloadable PDF file as an HTTP response.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are rendered in the response.
    """

    """
    UPDATE: should make this as a seperate function.
    This function will handle the invoice number and reset it every year on the 1st of April
    """
    # Retrieve the last used invoice number from the database.
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

    # Get the current date.
    current_date = datetime.date.today()

    # Calculate the next invoice number based on the last invoice in the database.
    if not invoice_num_db:
        # If there are no previous invoices, set the invoice_num to 1.
        invoice_num = 1
        if current_date.month < 4:
            year = current_date.year - 1
        else:
            year = current_date.year

    else:
        # If there are previous invoices, increment the invoice number by 1.
        # But reset the invoice number every year on the 1st of April.
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

    # Format the invoice number.
    invoice_num_formatted = f"INV-{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(invoice_num).zfill(6)}"
    IN_format = current_date.strftime("%d-%m-%Y")

    if request.method == "POST":
        # If the request method is POST, process the form data
        # Retrieve the form data
        invoice_data = request.form

        # Define various field sets for client, goods, and other information.
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

        # Check if all the fields are provided and not tampered with
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
            # Return an error message if any field is missing
            message = f"{', '.join(missing_fields)} not provided"
            return render_template("message.html", message=message), 403

        # Extract the goods data
        goods_data = {
            field: [value.strip() for value in invoice_data.getlist(field)]
            for field in goods_fields
        }

        # Check if all the required goods fields are provided
        required_goods_fields = {"descp": "", "qty": 0.001, "rate": 0.01, "gst": 0}
        missing_required_goods_fields = [
            key for key in required_goods_fields.keys() if not all(goods_data[key])
        ]
        if missing_required_goods_fields:
            # Return an error message if any required goods field is missing
            message = f"{', '.join(missing_required_goods_fields)} not provided"
            return render_template("message.html", message=message), 403

        # Convert the required goods fields to float and check if they are higher than their minimum values
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

        # Check if all the goods fields have the same length
        goods_data_length = {len(values) for values in goods_data.values()}
        if len(goods_data_length) != 1:
            message = f"All fields in the list of goods must have the same length and {', '.join(required_goods_fields.keys())} fields must be higher than their minimum values"
            return render_template("message.html", message=message), 403

        # Extract the client data
        clients_data = {
            field: invoice_data[field].strip()
            for field in clients_billing_fields + clients_shipping_fields + info_fields
        }

        # Validate PIN code in client data
        pncd_fields = ("baddrPncd", "saddrPncd")
        if any(
            not is_valid_pncd(clients_data[field])
            for field in pncd_fields
            if clients_data[field]
        ):
            message = "Invalid Pincode"
            return render_template("message.html", message=message), 403

        # Validate phone number in client data
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

        # Format client addresses
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

        # Format ETA
        if clients_data["eta"]:
            try:
                clients_data["eta"] = datetime.datetime.strptime(
                    clients_data["eta"], "%Y-%m-%d"
                ).strftime("%d-%m-%Y")
            except:
                message = f"Invalid values in ETA"
                return render_template("message.html", message=message), 403

        # Calculate various invoice totals and taxes
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

        # Retrieve company information from the database
        try:
            company_db = db.execute(
                "SELECT * FROM companies WHERE id = ?", session["company_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-COMP-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        company_db = company_db[0]

        # Format company address and phone numbers
        company_db["addr"] = " ".join(
            company_db[field] for field in address_fields if company_db[field]
        )
        company_db["phno"] = ", ".join(
            company_db[field] for field in phno_fields if company_db[field]
        )

        # Calculate GST with respect to company's residential state and client's residential state
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

        # Convert goods data to a list of dictionaries
        goods_data_list = [
            dict(zip(goods_data.keys(), values)) for values in zip(*goods_data.values())
        ]

        # Retrieve user information from the database
        try:
            user_db = db.execute(
                "SELECT username, type FROM users WHERE id = ?", session["user_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-NAME-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        # Render the invoice template with the data for PDF generation
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

        # Generate the PDF from the rendered invoice template
        pdf_options = {
            "page-size": "A4",
            "encoding": "UTF-8",
        }
        pdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

        # Define queries and parameters for selecting or inserting beneficiaries (clients).
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

        # Select or insert beneficiary (client) in the database
        ben_inv_id = None
        ben_ship_id = None
        if clients_data["bname"]:
            ben_inv_id = get_or_insert_ben(
                db,
                ben_select_query,
                ben_select_inv_params,
                ben_insert_query,
                ben_insert_inv_params,
            )
            if not isinstance(ben_inv_id, int):
                return handle_error(ben_inv_id)

        if (
            clients_data["bname"] == clients_data["sname"]
            and clients_data["bphno1"] == clients_data["sphno1"]
        ):
            ben_ship_id = ben_inv_id

        elif clients_data["sname"]:
            ben_ship_id = get_or_insert_ben(
                db,
                ben_select_query,
                ben_select_ship_params,
                ben_insert_query,
                ben_insert_ship_params,
            )
            if not isinstance(ben_ship_id, int):
                return handle_error(ben_ship_id)

        # Insert invoice data into the history table in the database.
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

        # Retrieve Information of goods from the database
        try:
            goods_data_db = db.execute(
                "SELECT id, descp FROM goods WHERE descp IN (?) AND company_id = ?",
                goods_data["descp"],
                session["company_id"],
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: INV-GOODS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        # Check if all goods are present in the database
        if len(goods_data_db) not in goods_data_length:
            # Add missing goods to the database
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

        # Link goods to the invoice in the database
        id_mapping = {item["descp"]: item["id"] for item in goods_data_db}
        goods_data_list = [
            {
                "qty": good["qty"],
                "amount": good["amount"],
                "id": id_mapping[good["descp"]],
            }
            for good in goods_data_list
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

        # Return the pdf to the user for download
        return send_file(
            BytesIO(pdf),
            mimetype="application/pdf",
            download_name=f"{invoice_num_formatted}.pdf",
            as_attachment=True,
        )

    else:
        # If the request is a GET request, render the invoice template
        return render_template(
            "invoice.html",
            invoice_num=invoice_num_formatted,
            invoice_date=IN_format,
            invoicenav=activepage,
        )


@app.route("/quotation", methods=["GET", "POST"])
@login_required
def quotation():
    """
    This function handles the generation of quotations.
    GET:
    - Retrieves the last used quotation number from the database and calculates the next quotation number.
    - Renders an HTML form for creating a new invoice with the calculated quotation number.
    POST:
    - Handles the form submission, validates the input data, and generates a PDF quotation.
    - It validates client and goods data, calculates various totals and taxes, and inserts the quotation and related information into the database.
    - Renders an HTML response containing the generated PDF for download.

    Parameters:
    - `GET` request:
        - None

    - `POST` request:
        - `request.form`: Form data containing client information, goods details, and other quotation-related data.

    Returns:
    - `GET` request:
        - Renders an HTML form to create a new quotation.

    - `POST` request:
        - Returns a downloadable PDF file as an HTTP response.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are rendered in the response.
    """

    """
    UPDATE: should make this as a seperate function.
    This function will handle the quotation number and reset it every year on the 1st of April
    """
    # Retrieve the last used invoice number from the database.
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

    # Get the current date.
    current_date = datetime.date.today()

    # Calculate the next quotation number based on the last quotation in the database.
    if not quotation_num_db:
        # If there are no previous quotations, set the quotation number to 1.
        quotation_num = 1
        if current_date.month < 4:
            year = current_date.year - 1
        else:
            year = current_date.year

    else:
        # If there are previous quotations, increment the quotation number by 1.
        # But reset the quotation number every year on the 1st of April.
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

    # Format the quotation number.
    quotation_num_formatted = f"EST-{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(quotation_num).zfill(6)}"
    IN_format = current_date.strftime("%d/%m/%Y")

    if request.method == "POST":
        # If the request method is POST, process the form data
        # Retrieve the form data
        quotation_data = request.form

        # Define various field sets for client, goods, and other information.
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

        # Check if all the fields are provided and not tampered with
        missing_fields = [
            field
            for field in clients_fields + goods_fields + info_fields + other_fields
            if quotation_data.get(field) is None
        ]
        if missing_fields:
            # Return an error message if any field is missing
            message = f"{', '.join(missing_fields)} not provided"
            return render_template("message.html", message=message), 403

        # Extract the goods data
        goods_data = {
            field: [value.strip() for value in quotation_data.getlist(field)]
            for field in goods_fields
        }

        # Check if all the required goods fields are provided
        required_goods_fields = {"descp": "", "qty": 0.001, "rate": 0.01, "gst": 0}
        missing_required_goods_fields = [
            key for key in required_goods_fields.keys() if not all(goods_data[key])
        ]
        if missing_required_goods_fields:
            # Return an error message if any required goods field is missing
            message = f"{', '.join(missing_required_goods_fields)} not provided"
            return render_template("message.html", message=message), 403

        # Convert the required goods fields to float and check if they are higher than their minimum values
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

        # Check if all the goods fields have the same length
        goods_data_length = {len(values) for values in goods_data.values()}
        if len(goods_data_length) != 1:
            message = f"All fields in the list of goods must have the same length and {', '.join(required_goods_fields.keys())} fields must be higher than their minimum values"
            return render_template("message.html", message=message), 403

        # Extract the client data
        clients_data = {
            field: quotation_data[field].strip()
            for field in clients_fields + info_fields
        }

        # Validate phone number in client data
        if clients_data["phno1"]:
            if not is_valid_phno(clients_data["phno1"]):
                message = "Invalid mobile number"
                return render_template("message.html", message=message), 403

        # Format ETA
        if clients_data["eta"]:
            try:
                clients_data["eta"] = datetime.datetime.strptime(
                    clients_data["eta"], "%Y-%m-%d"
                ).strftime("%d-%m-%Y")
            except:
                message = f"Invalid values in ETA"
                return render_template("message.html", message=message), 403

        # Calculate various invoice totals and taxes
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

        # Convert goods data to a list of dictionaries
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

        # Format company address and phone numbers
        company_db["addr"] = " ".join(
            company_db[field] for field in address_fields if company_db[field]
        )
        company_db["phno"] = ", ".join(
            company_db[field] for field in ("phno1", "phno2") if company_db[field]
        )

        # Retrieve user information from the database
        try:
            user_db = db.execute(
                "SELECT username, type FROM users WHERE id = ?", session["user_id"]
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: QUOT-NAME-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        # Render the invoice template with the data for PDF generation
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

        # Generate the PDF from the rendered invoice template
        pdf_options = {
            "page-size": "A4",
            "encoding": "UTF-8",
        }

        pdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

        # Define queries and parameters for selecting or inserting beneficiaries (clients).
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
        print(ben_insert_params)

        # Select or insert beneficiary (client) in the database
        ben_est_id = None
        if clients_data["qname"]:
            ben_est_id = get_or_insert_ben(
                db,
                ben_select_query,
                ben_select_params,
                ben_insert_query,
                ben_insert_params,
            )
            if not isinstance(ben_est_id, int):
                return handle_error(ben_est_id)

        # Insert invoice data into the history table in the database.
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

        # Retrieve Information of goods from the database
        try:
            goods_data_db = db.execute(
                "SELECT id, descp FROM goods WHERE descp IN (?) AND company_id = ?",
                goods_data["descp"],
                session["company_id"],
            )
        except Exception as e:
            message = f"Something went wrong, please try again.\nError-code: QUOT-GOODS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}"
            return render_template("message.html", message=message), 500

        # Check if all goods are present in the database
        if len(goods_data_db) not in goods_data_length:
            # Add missing goods to the database
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

        # Link goods to the invoice in the database
        id_mapping = {item["descp"]: item["id"] for item in goods_data_db}
        goods_data_list = [
            {
                "qty": good["qty"],
                "amount": good["amount"],
                "id": id_mapping[good["descp"]],
            }
            for good in goods_data_list
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

        # Return the pdf to the user for download
        return send_file(
            BytesIO(pdf),
            mimetype="application/pdf",
            download_name=f"{quotation_num_formatted}.pdf",
            as_attachment=True,
        )

    else:
        # If the request is a GET request, render the invoice template
        return render_template(
            "quote.html",
            quote_num=quotation_num_formatted,
            quote_date=IN_format,
            quotenav=activepage,
        )


@app.route("/inventory")
@login_required
def inventory():
    """
    This function renders the inventory page.
    GET:
    - Retrieves the goods data and beneficiaries data from the database.
    - Renders the inventory template with the data.

    Parameters:
    - `GET` request:
        - None

    Returns:
    - `GET` request:
        - Rendered inventory template.

    Exception Handling:
    - If an exception occurs during the query execution, it is handled and an error message is returned.
    """

    # SQL query to retrieve goods data
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

    # SQL query to retrieve beneficiaries data
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
        # Retrieve the goods data
        goods_list = db.execute(goods_query, session["company_id"])

        # Retrieve the beneficiaries data
        clients_list = db.execute(clients_query, session["company_id"])
    except Exception as e:
        # Return an error message if an exception occurs
        return apology(
            f"Something went wrong, please try again.\nError-code: INVN-MAT-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Set optional fields for goods data
    optional_goods_fields = ("hsn_sac", "uom")
    for good in goods_list:
        # Set optional fields to empty string if they are None
        good.update({k: good[k] or "" for k in optional_goods_fields})

    # Set address and phone number fields for beneficiaries data
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
        # Concatenate address fields with a space separator
        client["addr"] = " ".join(
            client[field] for field in address_fields if client[field]
        )
        # Concatenate phone number fields with a comma separator
        client["phno"] = ", ".join(
            client[field] for field in phno_fields if client[field]
        )
        # Set optional fields to empty string if they are None
        client.update({k: client[k] or "" for k in optional_clients_fields})

    # Render the inventory template with the processed data
    return render_template(
        "inventory.html",
        clients_list=clients_list,
        goods_list=goods_list,
        inventorynav=activepage,
    )


@app.route("/history")
@login_required
def history():
    """
    This function renders the history page.
    GET:
    - Retrieves history data from the database.
    - Renders the history template with the data.

    Parameters:
    - `GET` request:
        - None

    Returns:
    - `GET` request:
        - Rendered history template.

    Exception Handling:
    - If an exception occurs during the query execution, it is handled and an error message is returned.
    """

    # SQL query to retrieve the history data
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
        # Retrieve the history data
        history_list = db.execute(query, session["company_id"])
    except Exception as e:
        # Return an error message if an exception occurs
        return apology(
            f"Something went wrong, please try again.\nError-code: HIST-BILL-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Initialize lists to store invoice and quotation data
    invoice_list = []
    quotation_list = []
    current_history_id = None

    # Iterate through the history data and organize it into invoice and quotation lists
    for history in history_list:
        # Check if the current history entry is different from the previous one
        if history["id"] != current_history_id:
            # Update the current history ID
            current_history_id = history["id"]

            # Create a new dictionary entry for the history data
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

            # Append the entry to the appropriate list based on the history type
            if history["type"] == "Invoice":
                invoice_list.append(entry)
            else:
                quotation_list.append(entry)

        # Add the goods details to the list of goods for the current history entry
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

    # Render the history template with the invoice and quotation data
    return render_template(
        "history.html",
        invoice_list=invoice_list,
        quotation_list=quotation_list,
        historynav=activepage,
    )


@app.route("/settings")
@login_required
def settings():
    """
    This function renders the settings page.
    GET:
    - Retrieves Customer terms of the company data from the database.
    - Renders the settings template with the data.

    Parameters:
    - `GET` request:
        - None

    Returns:
    - `GET` request:
        - Rendered settings template.

    Exception Handling:
    - If an exception occurs during the query execution, it is handled and an error message is returned.
    """
    try:
        # Retrieve the customer terms from the database
        company_db = db.execute(
            "SELECT custTerms FROM companies WHERE id = ?", session["company_id"]
        )
    except Exception as e:
        # Return an error message if an exception occurs
        return apology(
            f"Something went wrong, please try again.\nError-code: SET-TERMS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Render the settings template with the retrieved data
    return render_template(
        "settings.html", company=company_db[0], settingsnav=activepage
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    This function handles the registration of new users.
    GET:
    - Renders an register template for creating a new user.
    POST:
    - Handles the form submission, validates the input data, and creates a new user in the database.

    Parameters:
    - `GET` request:
        - None

    - `POST` request:
        - `request.form`: Form data containing the user-related data.

    Returns:
    - `GET` request:
        - Rendered register template.

    - `POST` request:
        - Redirects the user to the company registration page.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are rendered in the response.
    """
    # Clear the session to ensure a clean state
    session.clear()

    if request.method == "POST":
        # If the request method is POST, process the login form
        # Get the register data from the form in dictionary structure
        register_data = request.form.to_dict()

        # Check if all fields are provided and not tampered
        register_fields = ["username", "password", "confirm-password", "email", "phno"]

        missing_fields = [
            field for field in register_fields if register_data.get(field) is None
        ]
        if missing_fields:
            # Return an error message if any fields is missing
            return apology(f"{', '.join(missing_fields)} not provided", 403)

        # Validate the register data
        # Check if username is valid and not already registered
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

        # Validate password
        if not is_valid_password(register_data["password"]):
            return apology(
                "Your password must be 8-24 characters long and include characters from at least two of the following categories: letters, numbers, special characters (including spaces), or even emojis.",
                403,
            )
        # Check if passwords match
        if register_data["password"] != register_data["confirm-password"]:
            return apology("Passwords must be same", 403)

        # Check the optional email is valid and not already registered when provided
        register_data["email"] = (
            register_data["email"].strip() if register_data["email"].strip() else None
        )
        if register_data["email"]:
            if not is_valid_email(register_data["email"]):
                return apology("Invalid email address", 403)
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

        # Check the optional phone number is valid and not already registered when provided
        if register_data["phno"]:
            if not is_valid_phno(register_data["phno"]):
                return apology("Invalid phone number", 403)
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
        else:
            register_data["phno"] = None

        # Insert the register data into the database
        register_data["password"] = generate_password_hash(register_data["password"])
        register_fields.remove("confirm-password")
        try:
            reg_id_db = db.execute(
                "INSERT INTO users (username, hash, email, phno, type) VALUES(?, ?, ?, ?, ?)",
                *(register_data[field] for field in register_fields),
                "admin",
            )
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: REG-USR-INS-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        # Log the user in
        session["user_id"] = reg_id_db

        # Flash a success message and redirect the user to the company registration page
        flash("User successfully registered")
        return redirect("/compregister")

    else:
        # If the request method is GET, render the register template
        # Flash a warning message and render the register template
        flash(
            "This page is only for Admins who wants to register themselves as well as their company. This page will be followed by a company registration form. For user registration, please contact your company admin. Thank you!"
        )
        return render_template("register.html", registernav=activepage)


@app.route("/compregister", methods=["GET", "POST"])
@user_required
def compregister():
    """
    This function handles the registration of new companies.
    GET:
    - Renders an company register template for creating a new company.
    POST:
    - Handles the form submission, validates the input data, and inserts the company data into the database.

    Parameters:
    - `GET` request:
        - None

    - `POST` request:
        - `request.form`: Form data containing the company-related data.

    Returns:
    - `GET` request:
        - Rendered company register template.

    - `POST` request:
        - Redirects the user to the home page.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are rendered in the response.

    Note:
    - This function is only accessible to admins who are logged in but not registered as a company.
    """
    if request.method == "POST":
        # If the request method is POST, process the login form
        # Get the company register data from the form
        compreg_data = request.form

        # Define required and optional fields
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

        # Check if all fields are provided and not tampered
        missing_fields = [
            field
            for field in required_fields + optional_fields
            if compreg_data.get(field) is None
        ]
        if missing_fields:
            # Return an error message if any fields is missing
            return apology(f"{', '.join(missing_fields)} not provided", 403)

        # Strip whitespace from form data
        compreg_data = {
            field: compreg_data[field].strip() if compreg_data[field].strip() else None
            for field in required_fields + optional_fields
        }

        # Check for missing required fields
        missing_required_fields = [
            field for field in required_fields if not compreg_data[field]
        ]
        if missing_required_fields:
            return apology(f"{', '.join(missing_required_fields)} not provided", 403)

        # Validate pincode
        if not is_valid_pncd(compreg_data["addrPncd"]):
            return apology("Invalid Pincode", 403)

        # Check the required phone number is valid and not already registered
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

        # Check the optional phone number is valid when provided
        if compreg_data["phno2"] and not is_valid_phno(compreg_data["phno2"]):
            return apology("Invalid phone number", 400)

        # Check the optional email is valid and not already registered when email is provided
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

        # Check the optional GSTIN is valid and not already registered when GSTIN is provided
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

        # Check the optional bank account number is valid and not already registered when bank account number is provided
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

        # Insert the company data into the database
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

        # Update the user's company ID
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

        # Store the company ID in the session
        session["company_id"] = regcomp_id_db

        # Flash a success message and redirect the user to the home page
        flash("Company is successfully registered")
        return redirect("/")

    else:
        # If the request method is GET
        # Check if the user is already registered in a company
        if session.get("company_id"):
            flash("Company is already registered")
            return redirect("/")

        # Retrieve the default terms from the database
        try:
            defaults_db = db.execute("SELECT custTerms FROM defaults")
        except Exception as e:
            return apology(
                f"Something went wrong, please try again.\nError-code: COMPREG-DEF-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
                500,
            )

        # Render the company registration page
        return render_template(
            "compregister.html", registernav=activepage, defaults=defaults_db[0]
        )


@app.route("/download_pdf/<int:pdf_id>")
@login_required
def download_pdf(pdf_id):
    """
    Endpoint to download a PDF file.

    Args:
        pdf_id (int): The ID of the PDF file to download.

    Returns:
        Response: The PDF file as a downloadable attachment.

    Raises:
        Exception: If an error occurs during the retrieval process.
    """
    try:
        # Retrieve the PDF data from the database
        pdf_data = db.execute(
            "SELECT bill_num, bill_timestamp, type, pdf FROM history WHERE id = ? AND company_id = ?",
            pdf_id,
            session["company_id"],
        )
    except Exception as e:
        # Handle any errors that occur during the retrieval process
        return apology(
            f"Something went wrong, please try again.\nError-code: DOWN-PDF-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    if pdf_data:
        # Extract relevant information from the PDF data
        pdf_data = pdf_data[0]
        bill_num_formatted = bill_num_formatr(
            pdf_data["type"], pdf_data["bill_timestamp"], pdf_data["bill_num"]
        )

        # Send the PDF file as a downloadable attachment
        return send_file(
            BytesIO(pdf_data["pdf"]),
            mimetype="application/pdf",
            download_name=f"{bill_num_formatted}.pdf",
            as_attachment=True,
        )

    else:
        # Handle the case when the PDF file is not found
        return apology("PDF not found", 404)


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    """
    Endpoint to change the user's password.

    Parameters:
    - `POST` request:
        - request.form: Form data containing the current password, new password, and confirm password.

    Returns:
    - `POST` request:
        - If the password change is successful, redirects the user to the settings page.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are returned in the response.
    """
    # Extract the form data
    passwords_data = request.form

    # Define the required fields for the form
    required_fields = ("current-password", "new-password", "confirm-password")

    # Check if any of the required fields are missing
    missing_fields = [
        field for field in required_fields if not passwords_data.get(field)
    ]

    # If any required field is missing, return an error message
    if missing_fields:
        return apology(f"{', '.join(missing_fields)} not provided", 403)

    # Check if the new password is valid
    if not is_valid_password(passwords_data["new-password"]):
        return apology(
            "Your password must be 8-24 characters long and include characters from at least two of the following categories: letters, numbers, special characters (including spaces).",
            403,
        )

    # Check if the new password and confirm password match
    if passwords_data["new-password"] != passwords_data["confirm-password"]:
        return apology("New Password and Confirm Password must be the same", 403)

    try:
        # Retrieve the hash of the user's current password from the database
        current_password_db = db.execute(
            "SELECT hash FROM users WHERE id = ?", session["user_id"]
        )
    except Exception as e:
        # If there is an error retrieving the current password, return an error message
        return apology(
            f"Something went wrong, please try again.\nError-code: CHNGPASS-PASS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Check if the current password matches the hash in the database
    if not check_password_hash(
        current_password_db[0]["hash"], passwords_data["current-password"]
    ):
        return apology("Current Password does not match", 400)

    try:
        # Update the new hash of the user's password in the database
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(passwords_data["new-password"]),
            session["user_id"],
        )
    except Exception as e:
        # If there is an error updating the password, return an error message
        return apology(
            f"Something went wrong, please try again.\nError-code: CHNGPASS-PASS-UPD-{type(e).__name__}.\nDEV-INFO: {e.args}",
            500,
        )

    # Show a success message and redirect to the settings page
    flash("Password changed successfully")
    return redirect("/settings")


@app.route("/change_terms", methods=["POST"])
def change_terms():
    """
    Endpoint to change the user's terms and conditions.

    Parameters:
    - `POST` request:
        - request.form: Form data containing the new terms and conditions.

    Returns:
    - `POST` request:
        - If the terms and conditions change is successful, redirects the user to the settings page.

    Exception Handling:
    - Various exceptions are caught, and appropriate error messages are returned in the response.
    """
    # Extract the form data
    terms_data = request.form

    # Check if the new terms and conditions field are provided and not tampered with
    if terms_data.get("new-terms") is None:
        return apology("New Terms and Conditions not provided", 403)

    # Update the user's terms and conditions in the database
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

    # Redirect to the settings page and Flash a success message
    flash("Terms and conditions changed successfully")
    return redirect("/settings")


@app.route("/apology/<string:message>/<code>")
def apology(message, code):
    """
    This function handles the error request from the invoice and quotations pages.

    Parameters:
    - `GET` request:
        - message (str): The error message to display.
        - code (int): The error code.

    Returns:
    - `GET` request:
        - The apology page.
    """

    # Unescape the error message to remove any HTML entities
    message = html.unescape(message)

    # Print the error message (for debugging purposes)
    print(message)

    def escape(s):
        """
        Escape special characters in the error message.

        This function replaces special characters with their corresponding escape sequences.
        The escape sequences are defined in the `old` and `new` lists.

        Reference: https://github.com/jacebrowning/memegen#special-characters

        Parameters:
        - s (str): The error message to escape.

        Returns:
        - str: The escaped error message.
        """

        # Define the special characters and their escape sequences
        special_characters = [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]

        # Replace each special character with its escape sequence
        for old, new in special_characters:
            s = s.replace(old, new)

        return s

    # Render the apology page template with the escaped error message and error code
    return render_template("apology.html", top=code, bottom=escape(message)), code
