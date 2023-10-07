document.addEventListener("DOMContentLoaded", () => {
	let serialNumber = 1;

	// Get references to DOM elements (statically generated)
	const invoiceForm = document.getElementById("invoice-form");
	const invoiceListOfGoods = document.getElementById("invoice-list-of-goods");
	const invoiceAddRow = document.getElementById("invoice-add-row");
	const invoiceRemoveRow = document.getElementById("invoice-remove-row");
	const shippingInfoCheck = document.getElementById("shipping-info-check");
	const shippingAddressCheck = document.getElementById("shipping-address-check");
	const billingInfoarray = Array.from(
		document.querySelectorAll("#billing-info > *:nth-child(even) > :first-child")
	).slice(0, 3);
	const shippingInfoarray = Array.from(document.querySelectorAll("#shipping-info > *:nth-child(even) > :first-child"));
	const billingAddressarray = Array.from(document.querySelectorAll("#billing-address > * > :first-child"));
	const shippingAddressarray = Array.from(document.querySelectorAll("#shipping-address > * > :first-child"));
	const totalAmount = document.getElementById("total-amount");

	// Cache frequently accessed elements (dynamically generated)
	const qtyElements = [];
	const rateElements = [];
	const amountElements = [];

	// Event listener for input changes
	invoiceForm.addEventListener("input", handleInputChange);

	// Event listener for click events
	invoiceForm.addEventListener("click", handleClick);

	// Event listener for change events
	invoiceForm.addEventListener("change", handleChange);

	// Event listener for submit events
	invoiceForm.addEventListener("submit", handleSubmit);

	// Generate the first row
	generateRow();

	/**
	 * Generates a new row of HTML elements for the invoice list of goods.
	 *
	 * @return {void} This function does not return a value.
	 */
	function generateRow() {
		const rowHTML = `
		<div class="pb-md-1" id="invoice${serialNumber}">
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
		invoiceListOfGoods.insertAdjacentHTML("beforeend", rowHTML);

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
		const billingInfoIndex = billingInfoarray.indexOf(target);
		const billingAddressIndex = billingAddressarray.indexOf(target);
		if (target.matches("[id^='qty']") || target.matches("[id^='rate']")) {
			updateAmount(target);
			updateTotalAmount();
		} else if (billingInfoIndex !== -1) {
			updateShippingInfo(billingInfoIndex);
		} else if (billingAddressIndex !== -1) {
			updateShippingAddress(billingAddressIndex);
		}
	}

	/**
	 * Handles the click event.
	 *
	 * @param {Event} event - The click event object.
	 */
	function handleClick(event) {
		const target = event.target;
		if (target === invoiceAddRow) {
			generateRow();
		} else if (target === invoiceRemoveRow && serialNumber > 2) {
			invoiceListOfGoods.removeChild(invoiceListOfGoods.lastElementChild);
			serialNumber--;
		}
	}

	/**
	 * Handles the change event.
	 *
	 * @param {Event} event - The event object.
	 */
	function handleChange(event) {
		const target = event.target;
		if (target === shippingInfoCheck) {
			copyShippingInfo();
		} else if (target === shippingAddressCheck) {
			copyShippingAddress();
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
	 * Copies the shipping information to the billing information if the shipping information checkbox is checked. Otherwise, clears the billing information.
	 */
	function copyShippingInfo() {
		const isChecked = shippingInfoCheck.checked;
		shippingInfoarray.forEach((info, i) => {
			info.value = isChecked ? billingInfoarray[i].value : "";
		});
	}

	/**
	 * Copies the shipping address to the billing address if the shipping address checkbox is checked.
	 */
	function copyShippingAddress() {
		const isChecked = shippingAddressCheck.checked;
		shippingAddressarray.forEach((address, i) => {
			address.value = isChecked ? billingAddressarray[i].value : "";
		});
	}

	/**
	 * Updates the shipping information based on the provided billing info index.
	 *
	 * @param {number} billingInfoIndex - The index of the billing info to update.
	 */
	function updateShippingInfo(billingInfoIndex) {
		shippingInfoarray[billingInfoIndex].value = shippingInfoCheck.checked
			? billingInfoarray[billingInfoIndex].value
			: "";
	}

	/**
	 * Updates the shipping address based on the selected billing address.
	 *
	 * @param {number} billingAddressIndex - The index of the billing address to update the shipping address from.
	 */
	function updateShippingAddress(billingAddressIndex) {
		shippingAddressarray[billingAddressIndex].value = shippingAddressCheck.checked
			? billingAddressarray[billingAddressIndex].value
			: "";
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

	function handleSubmit(event) {
		if (!invoiceForm.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}
		else {
			setTimeout(location.reload(), 5000);
		}
		invoiceForm.classList.add("was-validated");
	}
});
