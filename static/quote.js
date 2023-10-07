document.addEventListener("DOMContentLoaded", () => {
	let serialNumber = 1;

	// Get references to DOM elements (statically generated)
	const quoteForm = document.getElementById("quote-form");
	const quoteListOfGoods = document.getElementById("quote-list-of-goods");
	const totalAmount = document.getElementById("total-amount");
	const quoteAddRow = document.getElementById("quote-add-row");
	const quoteRemoveRow = document.getElementById("quote-remove-row");
	const quoteSubmit = document.getElementById("quote-submit");


	// Cache frequently accessed elements
	const qtyElements = [];
	const rateElements = [];
	const amountElements = [];

	// Event listener for input changes
	quoteForm.addEventListener("input", handleInputChange);

	// Event listener for click events
	quoteForm.addEventListener("click", handleClick);

	// Event listener for submit events
	quoteForm.addEventListener("submit", handleSubmit);

	// Generate the first row
	generateRow();

	/**
	 * Generates a new row of HTML elements for the invoice list of goods.
	 *
	 * @return {void} This function does not return a value.
	 */
	function generateRow() {
		const rowHTML = `
		<div class="pb-md-1" id="quote${serialNumber}">
			<div class="row g-0">
				<label class="col col-form-label d-md-none fs-5 fw-semibold fst-italic pt-3">Item No.</label>
			</div>
			<div class="row g-1">
				<div class="col-md-1">
					<div class="input-group">
						<span class="input-group-text">#</span>
						<input
							class="form-control"
							type="number"
							name="serialNumber"
							id="serialNumber"
							placeholder="S.No"
							value="${serialNumber}"
							readonly />
					</div>
				</div>
				<div class="col-md">
					<input class="form-control" type="text" name="desc" placeholder="Description of goods" required />
					<div class="invalid-feedback">Please enter the name of the item.</div>
				</div>
				<div class="col-md-1">
					<input class="form-control" type="text" name="hsn_sac" placeholder="HSN/SAC" />
				</div>
				<div class="col-md-1">
					<input
						class="form-control"
						type="number"
						name="qty"
						id="qty${serialNumber}"
						placeholder="Qty"
						min="0.001"
						step="0.001"
						required />
					<div class="invalid-feedback">Please enter the quantity.</div>
				</div>
				<div class="col-md-1">
					<input class="form-control" type="text" name="uom" placeholder="UOM" />
				</div>
				<div class="col-md-1">
					<div class="input-group has-validation">
						<span class="input-group-text">₹</span>
						<input
							class="form-control"
							type="number"
							name="rate"
							id="rate${serialNumber}"
							placeholder="Rate"
							min="0.01"
							step="0.01"
							required />
						<div class="invalid-feedback">Please enter the rate.</div>
					</div>
				</div>
				<div class="col-md-1">
					<div class="input-group">
						<span class="input-group-text">₹</span>
						<input
							class="form-control"
							type="number"
							name="amount"
							id="amount${serialNumber}"
							placeholder="Amount"
							readonly />
					</div>
				</div>
				<div class="col-md-1">
					<div class="input-group has-validation">
						<input class="form-control" type="number" name="gst" placeholder="GST" min="0" max="100" step="0.01" required />
						<span class="input-group-text">%</span>
						<div class="invalid-feedback">Please enter the GST.</div>
					</div>
				</div>
			</div>
		</div>
		`;

		// Append into the DOM
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

	/**
	 * Reloads the quote after a delay.
	 *
	 * @param {type} None - No parameters are needed.
	 * @return {type} None - No return value.
	 */
	function reloadQuote() {
		setTimeout(location.reload(), 1000);
	}

	function handleSubmit(event) {
		if (!quoteForm.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}
		else {
			setTimeout(location.reload(), 5000);
		}
		quoteForm.classList.add("was-validated");
	}
});
