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

	// Generate the first row
	generateRow();

	/**
	 * Generates a new row of HTML elements for the invoice list of goods.
	 *
	 * @return {void} This function does not return a value.
	 */
	function generateRow() {
		const rowHTML = `
		<div class="row g-1" id="invoice${serialNumber}">
			<div class="col text-center d-lg-none">Item No.</div>
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
});
