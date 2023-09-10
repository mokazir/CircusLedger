document.addEventListener("DOMContentLoaded", () => {
	// sno has be initialized to 0 and tweaked later
	let sno = 1;
	const invoiceform = document.getElementById("invoiceform");
	// const invoiceformlist = document.getElementById("invoiceformlist");
	const invoicelistofgoods = document.getElementById("invoicelistofgoods");
	const invoiceaddrow = document.getElementById("invoiceaddrow");
	const invoiceremoverow = document.getElementById("invoiceremoverow");
	const invoicecheckbi = document.getElementById("billinginfo");
	const invoicecheckba = document.getElementById("billingaddress");

	// Cache frequently accessed elements
	const qtyElements = [];
	const rateElements = [];
	const amountElements = [];

	// Generate the first row
	const generateRow = () => {
		const rowHTML = `
		<div class="row g-1" id="invoice${sno}">
			<div class="col text-center d-lg-none">Item No.</div>
			<div class="col-md-1">
				<input class="form-control" type="number" name="sno" id="sno" placeholder="S.No" value="${sno}" disabled />
			</div>
			<div class="col-md">
				<input class="form-control" type="text" name="desc" placeholder="Description of goods" value="" list="icf" />
			</div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="hsn_sac" placeholder="HSN/SAC" value="" />
			</div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="qty" id="qty${sno}" placeholder="Qty" value="" />
			</div>
			<div class="col-md-1"><input class="form-control" type="text" name="uom" placeholder="UOM" value="" /></div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="rate" id="rate${sno}" placeholder="Rate" value="" />
			</div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="amount" id="amount${sno}" placeholder="Amount" value="" />
			</div>
			<div class="col-md-1"><input class="form-control" type="text" name="gst" placeholder="GST" value="" /></div>
		</div>
		`;
		invoicelistofgoods.insertAdjacentHTML("beforeend", rowHTML);

		// const parser = new DOMParser();
		// const doc = parser.parseFromString(rowHTML, "text/html");
		// invoiceformlist.append(doc.body);

		// Cache elements for the new row
		qtyElements[sno] = document.getElementById(`qty${sno}`);
		// console.log(qtyElements);
		rateElements[sno] = document.getElementById(`rate${sno}`);
		amountElements[sno] = document.getElementById(`amount${sno}`);

		sno++;
	};

	// const generateRow = () => {
	// 	const newTemplate = quotelisttemplate.cloneNode(true);
	// 	newTemplate.classList.remove("d-none");
	// 	newTemplate.setAttribute("id", `quote${sno}`);
	// 	newTemplate.children[1].firstElementChild.value = parseInt(newTemplate.children[1].firstElementChild.value) + sno;
	// 	newTemplate.children[4].firstElementChild.id = `qty${sno}`;
	// 	newTemplate.children[6].firstElementChild.id = `rate${sno}`;
	// 	newTemplate.children[7].firstElementChild.id = `amount${sno}`;
	// 	invoiceformlist.appendChild(newTemplate);

	// 	// Cache elements for the new row
	// 	qtyElements[sno] = newTemplate.children[4].firstElementChild;
	// 	rateElements[sno] = newTemplate.children[6].firstElementChild;
	// 	amountElements[sno] = newTemplate.children[7].firstElementChild;

	// 	sno++;
	// };

	generateRow();
	invoiceform.addEventListener("keyup", (e) => {
		const target = e.target;
		if (!target.matches("[id^='qty']") && !target.matches("[id^='rate']")) {
			return;
		}
		const rowId = parseInt(target.id.match(/\d+/)[0]);
		// console.log(rowId);

		if (qtyElements[rowId].value && rateElements[rowId].value) {
			let amount = qtyElements[rowId].value * rateElements[rowId].value;
			amountElements[rowId].value = amount.toFixed(2);
		} else {
			amountElements[rowId].value = "";
		}
	});

	invoiceform.addEventListener("click", (e) => {
		const target = e.target;
		// console.log(target);
		// console.log(invoiceaddrow);
		if (target === invoiceaddrow) {
			generateRow();
		} else if (target === invoiceremoverow && sno > 2) {
			invoicelistofgoods.removeChild(invoicelistofgoods.lastElementChild);
			sno--;
		} else if (target === invoicecheckbi) {
			if (invoicecheckbi.checked === true) {
				document.getElementById("shippedcompanyname").value = document.getElementById("billedcompanyname").value;
				document.getElementById("sphno").value = document.getElementById("bphno").value;
				document.getElementById("sphno1").value = document.getElementById("bphno1").value;
			} else {
				document.getElementById("shippedcompanyname").value = "";
				document.getElementById("sphno").value = "";
				document.getElementById("sphno1").value = "";
			}
		} else if (target === invoicecheckba) {
			if (invoicecheckba.checked === true) {
				document.getElementById("saddrBnm").value = document.getElementById("baddrBnm").value;
				document.getElementById("saddrBno").value = document.getElementById("baddrBno").value;
				document.getElementById("saddrFlno").value = document.getElementById("baddrFlno").value;
				document.getElementById("saddrSt").value = document.getElementById("baddrSt").value;
				document.getElementById("saddrLoc").value = document.getElementById("baddrLoc").value;
				document.getElementById("saddrDist").value = document.getElementById("baddrDist").value;
				document.getElementById("saddrState").value = document.getElementById("baddrState").value;
				document.getElementById("saddrPncd").value = document.getElementById("baddrPncd").value;
			} else {
				document.getElementById("saddrBnm").value = "";
				document.getElementById("saddrBno").value = "";
				document.getElementById("saddrFlno").value = "";
				document.getElementById("saddrSt").value = "";
				document.getElementById("saddrLoc").value = "";
				document.getElementById("saddrDist").value = "";
				document.getElementById("saddrState").value = "";
				document.getElementById("saddrPncd").value = "";
			}
		}
	});

	// // Function to add a row
	// invoiceaddrow.addEventListener("click", () => {
	// 	generateRow();
	// });

	// // Function to remove a row
	// invoiceremoverow.addEventListener("click", () => {
	// 	if (sno > 2) {
	// 		invoiceformlist.removeChild(invoiceformlist.lastElementChild);
	// 		sno--;
	// 	}
	// });
});
