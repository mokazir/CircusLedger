# @app.route("/quote", methods=["GET", "POST"])
# @login_required
# def quote():
#     """Generate a quotation and send it to the user"""

#     # Get the last quotation number which is in the format of financial years-month-six digit number
#     quote_num = db.execute(
#         "SELECT bill_num FROM history WHERE company_id = ? and type = ? ORDER BY id DESC LIMIT 1",
#         session["company_id"],
#         "Quotation",
#     )

#     # Reset the quotation number every year on the 1st of April
#     current_date = datetime.date.today()

#     if len(quote_num) == 0:
#         quote_num = 1
#         if current_date.month < 4:
#             year = current_date.year - 1
#         else:
#             year = current_date.year

#     else:
#         if current_date.month < 4:
#             year = current_date.year - 1
#             quote_num = int(quote_num[0]["bill_num"][-6:]) + 1

#         else:
#             year = current_date.year
#             if quote_num[0]["bill_num"][3:5] == str(current_date.year):
#                 quote_num = 1
#             else:
#                 quote_num = int(quote_num[0]["bill_num"][-6:]) + 1

#     quotation_num_db = f"{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(quote_num).zfill(6)}"
#     quote_num_formatted = f"EST-{quotation_num_db}"
#     IN_format = current_date.strftime("%d/%m/%Y")

#     # User reached route via POST (as by submitting a form via POST)
#     if request.method == "POST":
#         quotedata = request.form
#         # print(quotedata)

#         company = db.execute(
#             "SELECT * FROM companies WHERE id = ?", session["company_id"]
#         )
#         company = company[0]
#         company["addr"] = (
#             company["addrBnm"]
#             + " "
#             + company["addrBno"]
#             + " "
#             + company["addrFlno"]
#             + " "
#             + company["addrSt"]
#             + " "
#             + company["addrLoc"]
#             + " "
#             + company["addrDist"]
#             + "-"
#             + company["addrPncd"]
#             + " "
#             + company["addrState"]
#         )
#         company["phno"] = company["phno1"] + ", " + company["phno2"]

#         temp = {
#             "serialNumber": quotedata.getlist("serialNumber"),
#             "desc": quotedata.getlist("desc"),
#             "hsn_sac": quotedata.getlist("hsn_sac"),
#             "qty": quotedata.getlist("qty"),
#             "uom": quotedata.getlist("uom"),
#             "rate": quotedata.getlist("rate"),
#             "gst": quotedata.getlist("gst"),
#         }

#         # Convert the strings to floats and round to 2 decimal places
#         temp["qty"] = [round(float(item), 2) for item in temp["qty"]]
#         temp["rate"] = [round(float(item), 2) for item in temp["rate"]]
#         temp["gst"] = [round(float(item), 2) for item in temp["gst"]]

#         temp["amount"] = []
#         for i in range(len(temp["serialNumber"])):
#             temp["amount"].append(round(temp["rate"][i] * temp["qty"][i], 2))

#         quotedata1 = {}

#         quotedata1["total-amount"] = round(sum(temp["amount"]), 2)
#         quotedata1["grand-total"] = round(quotedata1["total-amount"])
#         quotedata1["round-off"] = round(
#             quotedata1["total-amount"] - quotedata1["grand-total"]
#         )

#         temp["cgstrate"] = []
#         temp["cgstamount"] = []
#         temp["sgstrate"] = []
#         temp["sgstamount"] = []
#         total = {}
#         total["qty"] = 0
#         total["amount"] = 0
#         total["cgstamount"] = 0
#         total["sgstamount"] = 0
#         ograte = []
#         # Calculate rate and amount in temp without gst
#         for i in range(len(temp["serialNumber"])):
#             ograte.append(temp["rate"][i])
#             temp["rate"][i] = round(temp["rate"][i] * (1 - (temp["gst"][i] / 100)), 2)
#             temp["amount"][i] = round(temp["rate"][i] * temp["qty"][i], 2)
#             temp["cgstrate"].append(round(temp["gst"][i] / 2, 2))
#             temp["cgstamount"].append(
#                 round((temp["cgstrate"][i] / 100) * temp["amount"][i], 2)
#             )
#             total["qty"] += temp["qty"][i]
#             total["amount"] += temp["amount"][i]
#             total["cgstamount"] += temp["cgstamount"][i]
#             temp["sgstrate"].append(round(temp["gst"][i] / 2, 2))
#             temp["sgstamount"].append(
#                 round((temp["sgstrate"][i] / 100) * temp["amount"][i], 2)
#             )
#             total["sgstamount"] += temp["sgstamount"][i]

#         quotedata1["amountwords"] = (
#             num2words(
#                 quotedata1["total-amount"],
#                 lang="en_IN",
#                 to="currency",
#                 currency="INR",
#             ).title()
#             + " Only"
#         )

#         items = [dict(zip(temp, values)) for values in zip(*temp.values())]

#         rendered_template = render_template(
#             "cl_quote_template_custom.html",
#             company=company,
#             quotedata=quotedata,
#             quotedata1=quotedata1,
#             items=items,
#             quote_num=quote_num_formatted,
#             quote_date=IN_format,
#             total=total,
#         )

#         # Configure pdfkit options
#         pdf_options = {
#             "page-size": "A4",
#             # "margin-top": "0mm",
#             # "margin-right": "0mm",
#             # "margin-bottom": "0mm",
#             # "margin-left": "0mm",
#             "encoding": "UTF-8",
#             # # "no-outline": None,
#         }

#         # send response to browser as pdf
#         quotepdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

#         # When new beneficiary is added, add that to beneficiaries table in database
#         ben_est_id = db.execute(
#             "SELECT id FROM beneficiaries WHERE name = ? AND company_id = ?",
#             quotedata["quoted_to"],
#             session["company_id"],
#         )

#         try:
#             ben_est_id = ben_est_id[0]["id"]
#         except:
#             ben_est_id = db.execute(
#                 "INSERT INTO beneficiaries (name, phno1, type, company_id, added_by) VALUES (?, ?, ?, ?, ?)",
#                 quotedata["quoted_to"],
#                 quotedata["phno"],
#                 "quoted",
#                 session["company_id"],
#                 session["user_id"],
#             )
#             # print(ben_est_id)

#         # Store history in database
#         history_id = db.execute(
#             "INSERT INTO history (bill_num, type, billed_to, eta, amount, pdf, company_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#             quotation_num_db,
#             "Quotation",
#             ben_est_id,
#             quotedata["eta"],
#             quotedata1["grand-total"],
#             quotepdf,
#             session["company_id"],
#             session["user_id"],
#         )

#         if not history_id:
#             return apology("Something went wrong", 500)

#         # When new goods is added, add that to goods table in database
#         for i in range(len(items)):
#             dbitemid = db.execute(
#                 "SELECT id FROM goods WHERE desc = ? AND company_id = ?",
#                 items[i]["desc"],
#                 session["company_id"],
#             )

#             try:
#                 dbitemid = dbitemid[0]["id"]
#             except:
#                 dbitemid = db.execute(
#                     "INSERT INTO goods (desc, hsn_sac, uom, rate, gst, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                     items[i]["desc"],
#                     items[i]["hsn_sac"],
#                     items[i]["uom"],
#                     ograte[i],
#                     items[i]["gst"],
#                     session["company_id"],
#                     session["user_id"],
#                 )

#             db.execute(
#                 "INSERT INTO history_goods (history_id, goods_id, qty) VALUES (?, ?, ?)",
#                 history_id,
#                 dbitemid,
#                 items[i]["qty"],
#             )

#         # send quote as pdf
#         # import io
#         return send_file(
#             io.BytesIO(quotepdf),
#             mimetype="application/pdf",
#             download_name=f"{quote_num_formatted}.pdf",
#             as_attachment=True,
#         )

#     # User reached route via GET (as by clicking a link or via redirect)
#     else:
#         return render_template(
#             "quote.html",
#             quote_num=quote_num_formatted,
#             quote_date=IN_format,
#             quotenav=activepage,
#         )

# @app.route("/history")
# @login_required
# def history():
#     """Show billing history of the company"""
#     start = time.time()
#     company_id = session.get("company_id")

#     # Optimize SQL Queries
#     query = """
#     SELECT h.id, h.bill_num, h.bill_timestamp, h.type, b1.name AS billed_to, b2.name AS shipped_to, h.transport, h.payment, h.eta, h.amount
#     FROM history h
#     LEFT JOIN beneficiaries b1 ON h.billed_to = b1.id
#     LEFT JOIN beneficiaries b2 ON h.shipped_to = b2.id
#     WHERE h.company_id = ?
#     """
#     history_list = db.execute(query, company_id)

#     invoice_list = []
#     quotation_list = []

#     for history in history_list:
#         if history["type"] == "Invoice":
#             history["bill_num"] = bill_num_formatr(
#                 "Invoice", history["bill_timestamp"], history["bill_num"]
#             )
#             invoice_list.append(history)
#         else:
#             history["bill_num"] = bill_num_formatr(
#                 "Quotation", history["bill_timestamp"], history["bill_num"]
#             )
#             quotation_list.append(history)

#         history["list_of_goods"] = db.execute(
#             """
#             SELECT g.descp, g.hsn_sac, g.uom, g.rate, g.gst, hg.qty, hg.amount
#             FROM goods g
#             JOIN history_goods hg ON g.id = hg.goods_id
#             WHERE hg.history_id = ?
#             """,
#             history["id"],
#         )

#     end = time.time()
#     print(end - start)

#     return render_template(
#         "history.html",
#         invoice_list=invoice_list,
#         quotation_list=quotation_list,
#         historynav=activepage,
#     )


# @app.route("/history")
# @login_required
# def history():
#     """Show billing history of the company"""

#     query = """
#     SELECT
#         h.id,
#         CASE
#             WHEN h.type = 'Invoice' THEN 'INV-' || h.bill_num
#             ELSE 'EST-' || h.bill_num
#         END AS bill_num,
#         h.bill_timestamp,
#         h.type,
#         COALESCE(b1.name, '') AS billed_to,
#         COALESCE(b2.name, '') AS shipped_to,
#         h.transport,
#         h.payment,
#         h.eta,
#         h.amount,
#         json_group_array (
#             json_object (
#                 'descp',
#                 g.descp,
#                 'hsn_sac',
#                 g.hsn_sac,
#                 'uom',
#                 g.uom,
#                 'rate',
#                 g.rate,
#                 'gst',
#                 g.gst,
#                 'qty',
#                 hg.qty
#             )
#         ) AS list_of_goods
#     FROM
#         history AS h
#         LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
#         LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
#         LEFT JOIN history_goods AS hg ON h.id = hg.history_id
#         LEFT JOIN goods AS g ON hg.goods_id = g.id
#     WHERE
#         h.company_id = ?
#     GROUP BY
#         h.id,
#         h.bill_num,
#         h.bill_timestamp,
#         h.type,
#         billed_to,
#         shipped_to,
#         h.transport,
#         h.payment,
#         h.eta,
#         h.amount
#     ORDER BY
#         h.id DESC;
#     """

#     history_list = db.execute(query, session["company_id"])

#     invoice_list = [history for history in history_list if history["type"] == "Invoice"]
#     quotation_list = [history for history in history_list if history["type"] != "Invoice"]

#     history_list = [history.update({"list_of_goods": json.loads(history["list_of_goods"])}) for history in history_list]

#     return render_template(
#         "history.html",
#         invoice_list=invoice_list,
#         quotation_list=quotation_list,
#         historynav=activepage,
#     )


# @app.route("/invoice", methods=["GET", "POST"])
# @login_required
# def invoice():
#     """Generate a invoice and send it to the user"""

#     # Get the last invoice number which is in the format of financial years-month-six digit number
#     invoice_num = db.execute(
#         "SELECT bill_num FROM history WHERE company_id = ? and type = ? ORDER BY id DESC LIMIT 1",
#         session["company_id"],
#         "Invoice",
#     )

#     # Reset the invoice number every year on the 1st of April
#     current_date = datetime.date.today()

#     if len(invoice_num) == 0:
#         invoice_num = 1
#         if current_date.month < 4:
#             year = current_date.year - 1
#         else:
#             year = current_date.year

#     else:
#         if current_date.month < 4:
#             year = current_date.year - 1
#             invoice_num = int(invoice_num[0]["bill_num"][-6:]) + 1

#         else:
#             year = current_date.year
#             if invoice_num[0]["bill_num"][3:5] == str(current_date.year):
#                 invoice_num = 1
#             else:
#                 invoice_num = int(invoice_num[0]["bill_num"][-6:]) + 1

#     invoice_num_db = f"{str(year)[-2:]}/{str(year + 1)[-2:]}-{str(current_date.month).zfill(2)}-{str(invoice_num).zfill(6)}"
#     invoice_num_formatted = f"INV-{invoice_num_db}"
#     IN_format = current_date.strftime("%d/%m/%Y")

#     # User reached route via POST (as by submitting a form via POST)
#     if request.method == "POST":
#         invoice_data = request.form
#         # print(invoice_data)

#         company = db.execute(
#             "SELECT * FROM companies WHERE id = ?", session["company_id"]
#         )
#         company = company[0]
#         company["addr"] = (
#             company["addrBnm"]
#             + " "
#             + company["addrBno"]
#             + " "
#             + company["addrFlno"]
#             + " "
#             + company["addrSt"]
#             + " "
#             + company["addrLoc"]
#             + " "
#             + company["addrDist"]
#             + "-"
#             + company["addrPncd"]
#             + " "
#             + company["addrState"]
#         )
#         company["phno"] = company["phno1"] + ", " + company["phno2"]

#         invoicedata1 = {}

#         # Temporarily Create Sgstin Number
#         invoicedata1["sgstin"] = "8975463213079854"

#         invoicedata1["baddr"] = (
#             invoice_data["baddrBnm"]
#             + " "
#             + invoice_data["baddrBno"]
#             + " "
#             + invoice_data["baddrFlno"]
#             + " "
#             + invoice_data["baddrSt"]
#             + " "
#             + invoice_data["baddrLoc"]
#             + " "
#             + invoice_data["baddrDist"]
#             + "-"
#             + invoice_data["baddrPncd"]
#             + " "
#             + invoice_data["baddrState"]
#         )

#         invoicedata1["bphno"] = invoice_data["bphno"] + ", " + invoice_data["bphno1"]

#         invoicedata1["saddr"] = (
#             invoice_data["saddrBnm"]
#             + " "
#             + invoice_data["saddrBno"]
#             + " "
#             + invoice_data["saddrFlno"]
#             + " "
#             + invoice_data["saddrSt"]
#             + " "
#             + invoice_data["saddrLoc"]
#             + " "
#             + invoice_data["saddrDist"]
#             + "-"
#             + invoice_data["saddrPncd"]
#             + " "
#             + invoice_data["saddrState"]
#         )

#         invoicedata1["sphno"] = invoice_data["sphno"] + ", " + invoice_data["sphno1"]

#         temp = {
#             "serialNumber": invoice_data.getlist("serialNumber"),
#             "desc": invoice_data.getlist("desc"),
#             "hsn_sac": invoice_data.getlist("hsn_sac"),
#             "qty": invoice_data.getlist("qty"),
#             "uom": invoice_data.getlist("uom"),
#             "rate": invoice_data.getlist("rate"),
#             "gst": invoice_data.getlist("gst"),
#         }

#         # Convert the strings to floats and round to 2 decimal places
#         temp["qty"] = [round(float(item), 2) for item in temp["qty"]]
#         temp["rate"] = [round(float(item), 2) for item in temp["rate"]]
#         temp["gst"] = [round(float(item), 2) for item in temp["gst"]]

#         temp["amount"] = []
#         for i in range(len(temp["serialNumber"])):
#             temp["amount"].append(round(temp["rate"][i] * temp["qty"][i], 2))

#         invoicedata1["total-amount"] = round(sum(temp["amount"]), 2)
#         invoicedata1["grand-total"] = round(invoicedata1["total-amount"])
#         invoicedata1["round-off"] = round(
#             invoicedata1["total-amount"] - invoicedata1["grand-total"]
#         )

#         temp["cgstrate"] = []
#         temp["cgstamount"] = []
#         temp["sgstrate"] = []
#         temp["sgstamount"] = []
#         temp["igstrate"] = []
#         temp["igstamount"] = []
#         total = {}
#         total["qty"] = 0
#         total["amount"] = 0
#         total["cgstamount"] = 0
#         total["sgstamount"] = 0
#         total["igstamount"] = 0
#         ograte = []
#         # Calculate rate and amount in temp without gst
#         for i in range(len(temp["serialNumber"])):
#             ograte.append(temp["rate"][i])
#             temp["rate"][i] = round(temp["rate"][i] * (1 - (temp["gst"][i] / 100)), 2)
#             temp["amount"][i] = round(temp["rate"][i] * temp["qty"][i], 2)
#             temp["cgstrate"].append(round(temp["gst"][i] / 2, 2))
#             temp["cgstamount"].append(
#                 round((temp["cgstrate"][i] / 100) * temp["amount"][i], 2)
#             )
#             total["qty"] += temp["qty"][i]
#             total["amount"] += temp["amount"][i]
#             total["cgstamount"] += temp["cgstamount"][i]
#             if company["addrState"] == invoice_data["baddrState"]:
#                 temp["sgstrate"].append(round(temp["gst"][i] / 2, 2))
#                 temp["sgstamount"].append(
#                     round((temp["sgstrate"][i] / 100) * temp["amount"][i], 2)
#                 )
#                 temp["igstrate"].append("")
#                 temp["igstamount"].append("")
#                 total["sgstamount"] += temp["sgstamount"][i]
#             else:
#                 temp["igstrate"].append(round(temp["gst"][i], 2))
#                 temp["igstamount"].append(
#                     round((temp["igstrate"][i] / 100) * temp["amount"][i], 2)
#                 )
#                 temp["sgstrate"].append("")
#                 temp["sgstamount"].append("")
#                 total["igstamount"] += temp["igstamount"][i]

#         invoicedata1["amountwords"] = (
#             num2words(
#                 invoicedata1["total-amount"],
#                 lang="en_IN",
#                 to="currency",
#                 currency="INR",
#             ).title()
#             + " Only"
#         )

#         # Convert temp from dict of list to list of dict as items
#         # items = [
#         #     {key: value[i] for key, value in temp.items()}
#         #     for i in range(len(temp["serialNumber"]))
#         # ]
#         items = [dict(zip(temp, values)) for values in zip(*temp.values())]

#         rendered_template = render_template(
#             "cl_invoice_template_custom.html",
#             company=company,
#             invoice_data=invoice_data,
#             invoicedata1=invoicedata1,
#             items=items,
#             invoice_num=invoice_num_formatted,
#             invoice_date=IN_format,
#             total=total,
#         )

#         # Configure pdfkit options
#         pdf_options = {
#             "page-size": "A4",
#             # "margin-top": "0mm",
#             # "margin-right": "0mm",
#             # "margin-bottom": "0mm",
#             # "margin-left": "0mm",
#             "encoding": "UTF-8",
#             # # "no-outline": None,
#         }

#         # send response to browser as pdf
#         pdf = pdfkit.from_string(rendered_template, False, options=pdf_options)

#         # When new beneficiary is added, add that to beneficiaries table in database
#         if (
#             invoice_data["billed_to"] == invoice_data["shipped_to"]
#             and invoice_data["baddrBno"] == invoice_data["saddrBno"]
#         ):
#             ben_inv_id = db.execute(
#                 "SELECT id FROM beneficiaries WHERE name = ? AND company_id = ?",
#                 invoice_data["billed_to"],
#                 session["company_id"],
#             )

#             try:
#                 ben_inv_id = ben_inv_id[0]["id"]
#             except:
#                 ben_inv_id = db.execute(
#                     "INSERT INTO beneficiaries (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, type, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
#                     invoice_data["billed_to"],
#                     invoice_data["baddrBnm"],
#                     invoice_data["baddrBno"],
#                     invoice_data["baddrFlno"],
#                     invoice_data["baddrSt"],
#                     invoice_data["baddrLoc"],
#                     invoice_data["baddrDist"],
#                     invoice_data["baddrState"],
#                     invoice_data["baddrPncd"],
#                     invoice_data["bphno"],
#                     invoice_data["bphno1"],
#                     invoice_data["bgstin"],
#                     "billed",
#                     session["company_id"],
#                     session["user_id"],
#                 )
#             ben_ship_id = ben_inv_id

#         else:
#             ben_inv_id = db.execute(
#                 "SELECT id FROM beneficiaries WHERE name = ? AND addrBnm = ? AND company_id = ?",
#                 invoice_data["billed_to"],
#                 invoice_data["baddrBnm"],
#                 session["company_id"],
#             )

#             try:
#                 ben_inv_id = ben_inv_id[0]["id"]
#             except:
#                 ben_inv_id = db.execute(
#                     "INSERT INTO beneficiaries (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, type, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
#                     invoice_data["billed_to"],
#                     invoice_data["baddrBnm"],
#                     invoice_data["baddrBno"],
#                     invoice_data["baddrFlno"],
#                     invoice_data["baddrSt"],
#                     invoice_data["baddrLoc"],
#                     invoice_data["baddrDist"],
#                     invoice_data["baddrState"],
#                     invoice_data["baddrPncd"],
#                     invoice_data["bphno"],
#                     invoice_data["bphno1"],
#                     invoice_data["bgstin"],
#                     "invoiced",
#                     session["company_id"],
#                     session["user_id"],
#                 )

#             ben_ship_id = db.execute(
#                 "SELECT id FROM beneficiaries WHERE name = ? and addrBnm = ? AND company_id = ?",
#                 invoice_data["shipped_to"],
#                 invoice_data["saddrBnm"],
#                 session["company_id"],
#             )

#             try:
#                 ben_ship_id = ben_ship_id[0]["id"]
#             except:
#                 ben_ship_id = db.execute(
#                     "INSERT INTO beneficiaries (name, addrBnm, addrBno, addrFlno, addrSt, addrLoc, addrDist, addrState, addrPncd, phno1, phno2, gstin, type, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
#                     invoice_data["shipped_to"],
#                     invoice_data["saddrBnm"],
#                     invoice_data["saddrBno"],
#                     invoice_data["saddrFlno"],
#                     invoice_data["saddrSt"],
#                     invoice_data["saddrLoc"],
#                     invoice_data["saddrDist"],
#                     invoice_data["saddrState"],
#                     invoice_data["saddrPncd"],
#                     invoice_data["sphno"],
#                     invoice_data["sphno1"],
#                     invoicedata1["sgstin"],
#                     "shipped",
#                     session["company_id"],
#                     session["user_id"],
#                 )

#         # Store history in database
#         history_id = db.execute(
#             "INSERT INTO history (bill_num, type, billed_to, shipped_to, transport, payment, eta, amount, pdf, company_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
#             invoice_num_db,
#             "Invoice",
#             ben_inv_id,
#             ben_ship_id,
#             invoice_data["transport-mode"],
#             invoice_data["payment-mode"],
#             invoice_data["eta"],
#             invoicedata1["grand-total"],
#             pdf,
#             session["company_id"],
#             session["user_id"],
#         )

#         if not history_id:
#             return apology("Something went wrong", 500)

#         # When new items are added, add that to goods table in database
#         for i in range(len(items)):
#             dbitemid = db.execute(
#                 "SELECT id FROM goods WHERE desc = ? AND company_id = ?",
#                 items[i]["desc"],
#                 session["company_id"],
#             )

#             try:
#                 dbitemid = dbitemid[0]["id"]
#             except:
#                 dbitemid = db.execute(
#                     "INSERT INTO goods (desc, hsn_sac, uom, rate, gst, company_id, added_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                     items[i]["desc"],
#                     items[i]["hsn_sac"],
#                     items[i]["uom"],
#                     ograte[i],
#                     items[i]["gst"],
#                     session["company_id"],
#                     session["user_id"],
#                 )

#             db.execute(
#                 "INSERT INTO history_goods (history_id, goods_id, qty) VALUES (?, ?, ?)",
#                 history_id,
#                 dbitemid,
#                 items[i]["qty"],
#             )

#         # return invoice as pdf
#         # response = make_response(pdf)
#         # response.headers["Content-Type"] = "application/pdf"
#         # response.headers[
#         #     "Content-Disposition"
#         # ] = f"inline; filename={invoice_num_formatted}.pdf"
#         # return response
#         return send_file(
#             io.BytesIO(pdf),
#             mimetype="application/pdf",
#             download_name=f"{invoice_num_formatted}.pdf",
#             as_attachment=True,
#         )

#     # User reached route via GET (as by clicking a link or via redirect)
#     else:
#         return render_template(
#             "invoice.html",
#             invoice_num=invoice_num_formatted,
#             invoice_date=IN_format,
#             invoicenav=activepage,
#         )


# for field in float_list:
#     try:
#         goods_data[field] = [
#             float(item)
#             for item in goods_data[field]
#             if float(item) >= min_values[field]
#         ]
#     except ValueError:
#         message = f"Invalid {field} value"
#         return render_template("message.html", message=message), 403

#     if len(goods_data[field]) not in goods_data_length:
#         message = f"{field} cannot be less than {min_values[field]}"
#         return render_template("message.html", message=message), 403


# @app.route("/history")
# @login_required
# def history():
#     """Show billing history of the company"""

#     start = time.time()

#     query = """
#     SELECT h.id, h.bill_num, h.bill_timestamp, h.type, b1.name AS billed_to, b2.name AS shipped_to, h.transport, h.payment, h.eta, h.amount
#     FROM history h
#     LEFT JOIN beneficiaries b1 ON h.billed_to = b1.id
#     LEFT JOIN beneficiaries b2 ON h.shipped_to = b2.id
#     WHERE h.company_id = ? ORDER BY h.id DESC;
#     """
#     try:
#         history_list = db.execute(query, session["company_id"])
#     except Exception as e:
#         return apology(
#             f"Something went wrong, please try again.\nError-code: HIST-BILL-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
#             500,
#         )

#     invoice_list = []
#     quotation_list = []
#     optional_quotation_fields = {"billed_to", "eta"}
#     optional_invoice_fields = {
#         "shipped_to",
#         "transport",
#         "payment",
#     } | optional_quotation_fields
#     optional_goods_fields = {"hsn_sac", "uom"}

#     for history in history_list:
#         if history["type"] == "Invoice":
#             history["bill_num"] = bill_num_formatr(
#                 "Invoice", history["bill_timestamp"], history["bill_num"]
#             )
#             history.update(
#                 {
#                     k: history[k] if history[k] is not None else ""
#                     for k in optional_invoice_fields
#                 }
#             )
#             invoice_list.append(history)
#         else:
#             history["bill_num"] = bill_num_formatr(
#                 "Quotation", history["bill_timestamp"], history["bill_num"]
#             )
#             history.update(
#                 {
#                     k: history[k] if history[k] is not None else ""
#                     for k in optional_quotation_fields
#                 }
#             )
#             quotation_list.append(history)

#         try:
#             history["list_of_goods"] = db.execute(
#                 """
#                 SELECT g.descp, g.hsn_sac, g.uom, g.rate, g.gst, hg.qty, hg.amount
#                 FROM goods g
#                 LEFT JOIN history_goods hg ON g.id = hg.goods_id
#                 WHERE hg.history_id = ?
#                 """,
#                 history["id"],
#             )
#         except Exception as e:
#             return apology(
#                 f"Something went wrong, please try again.\nError-code: HIST-GOODS-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
#                 500,
#             )
#         for good in history["list_of_goods"]:
#             good.update(
#                 {
#                     k: good[k] if good[k] is not None else ""
#                     for k in optional_goods_fields
#                 }
#             )

#     end = time.time()
#     print(end - start)
#     return render_template(
#         "history.html",
#         invoice_list=invoice_list,
#         quotation_list=quotation_list,
#         historynav=activepage,
#     )


# @app.route("/history")
# @login_required
# def history():
#     """Show billing history of the company"""

#     start = time.time()

#     query = """
#     SELECT
#         h.id,
#         h.bill_num,
#         h.bill_timestamp,
#         h.type,
#         b1.name AS billed_to,
#         b2.name AS shipped_to,
#         h.transport,
#         h.payment,
#         h.eta,
#         h.amount,
#         json_group_array (
#             json_object (
#                 'descp',
#                 g.descp,
#                 'hsn_sac',
#                 g.hsn_sac,
#                 'uom',
#                 g.uom,
#                 'rate',
#                 g.rate,
#                 'gst',
#                 g.gst,
#                 'qty',
#                 hg.qty,
#                 'amount',
#                 hg.amount
#             )
#         ) AS list_of_goods
#     FROM
#         history AS h
#         LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
#         LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
#         LEFT JOIN history_goods AS hg ON h.id = hg.history_id
#         LEFT JOIN goods AS g ON hg.goods_id = g.id
#     WHERE
#         h.company_id = ?
#     GROUP BY
#         h.id
#     ORDER BY
#         h.id DESC;
#     """

#     try:
#         history_list = db.execute(query, session["company_id"])
#     except Exception as e:
#         return apology(
#             f"Something went wrong, please try again.\nError-code: HIST-BILL-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
#             500,
#         )

#     invoice_list = []
#     quotation_list = []
#     optional_quotation_fields = {"billed_to", "eta"}
#     optional_invoice_fields = {
#         "shipped_to",
#         "transport",
#         "payment",
#     } | optional_quotation_fields
#     optional_goods_fields = {"hsn_sac", "uom"}

#     for history in history_list:
#         history["bill_num"] = bill_num_formatr(
#             history["type"], history["bill_timestamp"], history["bill_num"]
#         )

#         history.update(
#             {
#                 k: history[k] if history[k] is not None else ""
#                 for k in optional_invoice_fields if history["type"] == "Invoice"
#             }
#         )
#         history.update(
#             {
#                 k: history[k] if history[k] is not None else ""
#                 for k in optional_quotation_fields if history["type"] != "Invoice"
#             }
#         )

#         history["list_of_goods"] = json.loads(history["list_of_goods"])

#         for good in history["list_of_goods"]:
#             good.update(
#                 {
#                     k: good[k] if good[k] is not None else ""
#                     for k in optional_goods_fields
#                 }
#             )

#         if history["type"] == "Invoice":
#             invoice_list.append(history)
#         else:
#             quotation_list.append(history)

#     end = time.time()
#     print(end - start)
#     return render_template(
#         "history.html",
#         invoice_list=invoice_list,
#         quotation_list=quotation_list,
#         historynav=activepage,
#     )


# @app.route("/")
# @login_required
# def index():
#     """Show homepage"""
#     start = time.time()
#     query = """
#     SELECT
#         h.id,
#         h.bill_num,
#         h.bill_timestamp,
#         h.type,
#         b1.name AS billed_to,
#         b2.name AS shipped_to,
#         h.transport,
#         h.payment,
#         h.eta,
#         h.amount,
#         json_group_array (
#             json_object (
#                 'descp',
#                 g.descp,
#                 'hsn_sac',
#                 g.hsn_sac,
#                 'uom',
#                 g.uom,
#                 'rate',
#                 g.rate,
#                 'gst',
#                 g.gst,
#                 'qty',
#                 hg.qty,
#                 'amount',
#                 hg.amount
#             )
#         ) AS list_of_goods
#     FROM
#         history AS h
#         LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
#         LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
#         LEFT JOIN history_goods AS hg ON h.id = hg.history_id
#         LEFT JOIN goods AS g ON hg.goods_id = g.id
#     WHERE
#         h.company_id = ? AND h.type = ?
#     GROUP BY
#         h.id
#     ORDER BY
#         h.id DESC
#     LIMIT
#         5;
#     """

#     try:
#         invoice_list = db.execute(query, session["company_id"], "Invoice")
#         quotation_list = db.execute(query, session["company_id"], "Quotation")
#     except Exception as e:
#         return apology(
#             f"Something went wrong, please try again.\nError-code: IND-HIST-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
#             500,
#         )

#     optional_quotation_fields = ("billed_to", "eta")
#     optional_invoice_fields = (
#         "shipped_to",
#         "transport",
#         "payment",
#     ) + optional_quotation_fields
#     optional_goods_fields = ("hsn_sac", "uom")

#     for history in invoice_list + quotation_list:
#         history["bill_num"] = bill_num_formatr(
#             history["type"], history["bill_timestamp"], history["bill_num"]
#         )
#         history["list_of_goods"] = json.loads(history["list_of_goods"])
#         history.update(
#             {
#                 k: history[k] or ""
#                 for k in optional_invoice_fields
#                 if history["type"] == "Invoice"
#             }
#         )
#         history.update(
#             {
#                 k: history[k] or ""
#                 for k in optional_quotation_fields
#                 if history["type"] == "Quotation"
#             }
#         )
#         for good in history["list_of_goods"]:
#             good.update(
#                 {
#                     k: good[k] or ""
#                     for k in optional_goods_fields
#                 }
#             )

#     end = time.time()
#     print(end - start)
#     return render_template(
#         "index.html",
#         invoice_list=invoice_list,
#         quotation_list=quotation_list,
#         homenav=activepage,
#     )


# @app.route("/")
# @login_required
# def index():
#     """Show homepage"""
#     start = time.time()
#     query = """
#     WITH
#         invoice_data AS (
#             SELECT
#                 h.id,
#                 h.bill_num,
#                 h.bill_timestamp,
#                 h.type,
#                 b1.name AS billed_to,
#                 b2.name AS shipped_to,
#                 h.transport,
#                 h.payment,
#                 h.eta,
#                 h.amount,
#                 json_group_array (
#                     json_object (
#                         'descp',
#                         g.descp,
#                         'hsn_sac',
#                         g.hsn_sac,
#                         'uom',
#                         g.uom,
#                         'rate',
#                         g.rate,
#                         'gst',
#                         g.gst,
#                         'qty',
#                         hg.qty
#                     )
#                 ) AS list_of_goods
#             FROM
#                 history AS h
#                 LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
#                 LEFT JOIN beneficiaries AS b2 ON h.shipped_to = b2.id
#                 LEFT JOIN history_goods AS hg ON h.id = hg.history_id
#                 LEFT JOIN goods AS g ON hg.goods_id = g.id
#             WHERE
#                 h.company_id = c.id
#                 AND h.type = 'Invoice'
#             GROUP BY
#                 h.id
#             ORDER BY
#                 h.id DESC
#             LIMIT
#                 5
#         ),
#         quotation_data AS (
#             SELECT
#                 h.id,
#                 h.bill_num AS bill_num,
#                 h.bill_timestamp,
#                 h.type,
#                 b1.name AS billed_to,
#                 h.eta,
#                 h.amount,
#                 json_group_array (
#                     json_object (
#                         'descp',
#                         g.descp,
#                         'hsn_sac',
#                         g.hsn_sac,
#                         'uom',
#                         g.uom,
#                         'rate',
#                         g.rate,
#                         'gst',
#                         g.gst,
#                         'qty',
#                         hg.qty
#                     )
#                 ) AS list_of_goods
#             FROM
#                 history AS h
#                 LEFT JOIN beneficiaries AS b1 ON h.billed_to = b1.id
#                 LEFT JOIN history_goods AS hg ON h.id = hg.history_id
#                 LEFT JOIN goods AS g ON hg.goods_id = g.id
#             WHERE
#                 h.company_id = c.id
#                 AND h.type = 'Quotation'
#             GROUP BY
#                 h.id
#             ORDER BY
#                 h.id DESC
#             LIMIT
#                 5
#         )
#     SELECT
#         (
#             SELECT
#                 json_group_array (
#                     json_object (
#                         'id',
#                         id,
#                         'bill_num',
#                         bill_num,
#                         'bill_timestamp',
#                         bill_timestamp,
#                         'type',
#                         type,
#                         'billed_to',
#                         billed_to,
#                         'shipped_to',
#                         shipped_to,
#                         'transport',
#                         transport,
#                         'payment',
#                         payment,
#                         'eta',
#                         eta,
#                         'amount',
#                         amount,
#                         'list_of_goods',
#                         list_of_goods
#                     )
#                 )
#             FROM
#                 invoice_data
#         ) AS invoices,
#         (
#             SELECT
#                 json_group_array (
#                     json_object (
#                         'id',
#                         id,
#                         'bill_num',
#                         bill_num,
#                         'bill_timestamp',
#                         bill_timestamp,
#                         'type',
#                         type,
#                         'billed_to',
#                         billed_to,
#                         'eta',
#                         eta,
#                         'amount',
#                         amount,
#                         'list_of_goods',
#                         list_of_goods
#                     )
#                 )
#             FROM
#                 quotation_data
#         ) AS quotations
#         FROM
#             companies AS c
#         WHERE
#             c.id = ?
#     """

#     try:
#         history_data = db.execute(query, session["company_id"])
#     except Exception as e:
#         return apology(
#             f"Something went wrong, please try again.\nError-code: IND-HIST-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
#             500,
#         )

#     optional_quotation_fields = ("billed_to", "eta")
#     optional_invoice_fields = (
#         "shipped_to",
#         "transport",
#         "payment",
#     ) + optional_quotation_fields
#     optional_goods_fields = ("hsn_sac", "uom")
#     invoice_list = json.loads(history_data[0]["invoices"])
#     quotation_list = json.loads(history_data[0]["quotations"])
#     for item in invoice_list + quotation_list:
#         item["bill_num"] = bill_num_formatr(item["type"], item["bill_timestamp"], item["bill_num"])
#         item["list_of_goods"] = json.loads(item["list_of_goods"])
#         item.update(
#             {
#                 k: item[k] if item[k] is not None else ""
#                 for k in optional_invoice_fields if item["type"] == "Invoice"
#             }
#         )
#         item.update(
#             {
#                 k: item[k] if item[k] is not None else ""
#                 for k in optional_quotation_fields if item["type"] != "Invoice"
#             }
#         )
#         for good in item["list_of_goods"]:
#             good.update(
#                 {
#                     k: good[k] if good[k] is not None else ""
#                     for k in optional_goods_fields
#                 }
#             )

#     end = time.time()
#     print(end - start)
#     return render_template(
#         "index.html",
#         invoice_list=invoice_list,
#         quotation_list=quotation_list,
#         homenav=activepage,
#     )


# @app.route("/inventory")
# @login_required
# def inventory():
#     """Show Inventory of goods and beneficiaries of the company"""
#     start = time.time()
#     query = """
#     WITH
#         goods_data AS (
#             SELECT
#                 g.descp,
#                 g.hsn_sac,
#                 g.uom,
#                 g.rate,
#                 g.gst,
#                 g.added_at,
#                 u1.username
#             FROM
#                 goods AS g
#                 JOIN users AS u1 ON g.added_by = u1.id
#             WHERE
#                 g.company_id = c.id
#         ),
#         clients_data AS (
#             SELECT
#                 b.name,
#                 COALESCE(
#                     b.addrBnm || ' ' || b.addrBno || ' ' || b.addrFlno || ' ' || b.addrSt || ' ' || b.addrLoc || ' ' || b.addrDist || '-' || b.addrPncd || ' ' || b.addrState,
#                     ''
#                 ) AS addr,
#                 COALESCE(b.phno1 || ', ' || b.phno2, '') AS phno,
#                 b.gstin,
#                 b.added_at,
#                 u2.username
#             FROM
#                 beneficiaries AS b
#                 JOIN users AS u2 ON b.added_by = u2.id
#             WHERE
#                 b.company_id = c.id
#         )
#     SELECT
#         (
#             SELECT
#                 json_group_array (
#                     json_object (
#                         'descp',
#                         descp,
#                         'hsn_sac',
#                         hsn_sac,
#                         'uom',
#                         uom,
#                         'rate',
#                         rate,
#                         'gst',
#                         gst,
#                         'added_at',
#                         added_at,
#                         'added_by',
#                         username
#                     )
#                 )
#             FROM
#                 goods_data
#         ) AS goods,
#         (
#             SELECT
#                 json_group_array (
#                     json_object (
#                         'name',
#                         name,
#                         'addr',
#                         addr,
#                         'phno',
#                         phno,
#                         'gstin',
#                         gstin,
#                         'added_at',
#                         added_at,
#                         'added_by',
#                         username
#                     )
#                 )
#             FROM
#                 clients_data
#         ) AS clients
#     FROM
#         companies AS c
#     WHERE
#         c.id = ?
#     """

#     try:
#         inventory_data = db.execute(query, session["company_id"])
#     except Exception as e:
#         return apology(
#             f"Something went wrong, please try again.\nError-code: INVN-MAT-RET-{type(e).__name__}.\nDEV-INFO: {e.args}",
#             500,
#         )

#     goods_list = json.loads(inventory_data[0]["goods"])
#     clients_list = json.loads(inventory_data[0]["clients"])

#     end = time.time()
#     print(end - start)
#     return render_template(
#         "inventory.html",
#         clients_list=clients_list,
#         goods_list=goods_list,
#         inventorynav=activepage,
#     )
