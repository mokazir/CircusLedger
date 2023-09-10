document.addEventListener("DOMContentLoaded", () => {
	// sno has be initialized to 0 and tweaked later
	let sno = 1;
	const quoteform = document.getElementById("quoteform");
	const quoteformlist = document.getElementById("quoteformlist");
	const quoteaddrow = document.getElementById("quoteaddrow");
	const quoteremoverow = document.getElementById("quoteremoverow");

	// Cache frequently accessed elements
	const qtyElements = [];
	const rateElements = [];
	const amountElements = [];

	// Generate the first row
	const generateRow = () => {
		const rowHTML = `
		<div class="row g-1" id="quote${sno}">
			<div class="col mt-3 text-center d-lg-none">Item.No</div>
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
		quoteformlist.insertAdjacentHTML("beforeend", rowHTML);

		// const parser = new DOMParser();
		// const doc = parser.parseFromString(rowHTML, "text/html");
		// quoteformlist.append(doc.body);

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
	// 	quoteformlist.appendChild(newTemplate);

	// 	// Cache elements for the new row
	// 	qtyElements[sno] = newTemplate.children[4].firstElementChild;
	// 	rateElements[sno] = newTemplate.children[6].firstElementChild;
	// 	amountElements[sno] = newTemplate.children[7].firstElementChild;

	// 	sno++;
	// };

	generateRow();
	quoteformlist.addEventListener("keyup", (e) => {
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

	quoteform.addEventListener("click", (e) => {
		const target = e.target;
		// console.log(target);
		// console.log(quoteaddrow);
		if (target === quoteaddrow) {
			generateRow();
		} else if (target === quoteremoverow && sno > 2) {
			quoteformlist.removeChild(quoteformlist.lastElementChild);
			sno--;
		}
	});

	// // Function to add a row
	// quoteaddrow.addEventListener("click", () => {
	// 	generateRow();
	// });

	// // Function to remove a row
	// quoteremoverow.addEventListener("click", () => {
	// 	if (sno > 2) {
	// 		quoteformlist.removeChild(quoteformlist.lastElementChild);
	// 		sno--;
	// 	}
	// });
});
