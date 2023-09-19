document.addEventListener("DOMContentLoaded", () => {
	// serialNumber has be initialized to 0 and tweaked later
	let serialNumber = 1;
	const quoteForm = document.getElementById("quote-form");
	const quoteListOfGoods = document.getElementById("quote-list-of-goods");
	const quoteAddRow = document.getElementById("quote-add-row");
	const quoteRemoveRow = document.getElementById("quote-remove-row");
	const totalAmount = document.getElementById("total-amount");

	// Cache frequently accessed elements
	const qtyElements = [];
	const rateElements = [];
	const amountElements = [];

	// Event listener for input changes
	quoteForm.addEventListener("input", handleInputChange);

	// Event listener for click events
	quoteForm.addEventListener("click", handleClick);

	// Generate the first row
	generateRow();

	/**
	 * Generates a new row of HTML elements for the invoice list of goods.
	 *
	 * @return {void} This function does not return a value.
	 */
	function generateRow() {
		const rowHTML = `
		<div class="row g-1" id="quote${serialNumber}">
			<div class="col text-center d-lg-none">Item.No</div>
			<div class="col-md-1">
				<input class="form-control" type="number" name="serialNumber" id="serialNumber" placeholder="S.No" value="${serialNumber}" disabled />
			</div>
			<div class="col-md">
				<input class="form-control" type="text" name="desc" placeholder="Description of goods" value="" list="icf" />
			</div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="hsn_sac" placeholder="HSN/SAC" value="" />
			</div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="qty" id="qty${serialNumber}" placeholder="Qty" value="" />
			</div>
			<div class="col-md-1"><input class="form-control" type="text" name="uom" placeholder="UOM" value="" /></div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="rate" id="rate${serialNumber}" placeholder="Rate" value="" />
			</div>
			<div class="col-md-1">
				<input class="form-control" type="text" name="amount" id="amount${serialNumber}" placeholder="Amount" value="" />
			</div>
			<div class="col-md-1"><input class="form-control" type="text" name="gst" placeholder="GST" value="" /></div>
		</div>
		`;
		quoteListOfGoods.insertAdjacentHTML("beforeend", rowHTML);

		// Cache elements for the new row
		qtyElements[serialNumber] = document.getElementById(`qty${serialNumber}`);
		rateElements[serialNumber] = document.getElementById(`rate${serialNumber}`);
		amountElements[serialNumber] = document.getElementById(`amount${serialNumber}`);

		serialNumber++;
	}

	/**
	 * Handles the input change event.
	 *
	 * @param {Event} event - The input change event object.
	 */
	function handleInputChange(event) {
		const target = event.target;
		if (target.matches("[id^='qty']") || target.matches("[id^='rate']")) {
			updateAmount(target);
			updateTotalAmount();
		}
	}

	/**
	 * Handles the click event.
	 *
	 * @param {Event} event - The click event object.
	 */
	function handleClick(event) {
		const target = event.target;
		if (target === quoteAddRow) {
			generateRow();
		} else if (target === quoteRemoveRow && serialNumber > 2) {
			quoteListOfGoods.removeChild(quoteListOfGoods.lastElementChild);
			serialNumber--;
		}
	}

	/**
	 * Updates the amount based on the target element.
	 *
	 * @param {Object} target - The target element.
	 */
	function updateAmount(target) {
		const rowId = parseInt(target.id.match(/\d+/)[0]);

		const qty = qtyElements[rowId].value;
		const rate = rateElements[rowId].value;
		const amount = qty && rate ? (qty * rate).toFixed(2) : "";

		amountElements[rowId].value = amount;
	}

	/**
	 * Updates the total amount based on the values of the amountElements.
	 *
	 * @param {type} paramName - description of parameter
	 * @return {type} description of return value
	 */
	function updateTotalAmount() {
		const total = amountElements.reduce(
			(acc, element) => acc + (element.value !== "" ? parseFloat(element.value) : 0),
			0
		);

		totalAmount.value = total === 0 ? "" : total.toFixed(2);
	}
});
