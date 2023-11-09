// When the DOM is loaded
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
	invoiceForm.addEventListener("input", handleInput);

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
		// Generate the HTML for the new row
		const rowHTML = `
		<div class="pb-md-1" id="invoice${serialNumber}">
			<!-- Item No. -->
			<div class="row g-0">
				<label class="col col-form-label d-md-none fs-5 fw-semibold fst-italic pt-3">Item No.</label>
			</div>
			<div class="row g-1">
				<!-- Serial Number -->
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
				<!-- Description of Goods -->
				<div class="col-md">
					<input class="form-control" type="text" name="descp" placeholder="Description of goods" required />
					<div class="invalid-feedback">Please enter the name of the item.</div>
				</div>
				<!-- HSN/SAC -->
				<div class="col-md-1">
					<input class="form-control" type="text" name="hsn_sac" placeholder="HSN/SAC" />
				</div>
				<!-- Quantity -->
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
				<!-- UOM -->
				<div class="col-md-1">
					<input class="form-control" type="text" name="uom" placeholder="UOM" />
				</div>
				<!-- Rate -->
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
				<!-- Amount -->
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
				<!-- GST -->
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

		// Append the new row to the DOM
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
	function handleInput(event) {
		// Get the target element from the event
		const target = event.target;

		// Find the index of the target element in the billingInfoarray
		const billingInfoIndex = billingInfoarray.indexOf(target);

		// Find the index of the target element in the billingAddressarray
		const billingAddressIndex = billingAddressarray.indexOf(target);

		// Check if the target element matches the pattern for quantity or rate inputs
		if (target.matches("[id^='qty']") || target.matches("[id^='rate']")) {
			// Update the amount based on the target element
			updateAmount(target);

			// Update the total amount
			updateTotalAmount();
		} else if (billingInfoIndex !== -1) {
			// Update the shipping info based on the billingInfoIndex
			updateShippingInfo(billingInfoIndex);
		} else if (billingAddressIndex !== -1) {
			// Update the shipping address based on the billingAddressIndex
			updateShippingAddress(billingAddressIndex);
		}
	}

	/**
	 * Handles the click event.
	 *
	 * @param {Event} event - The click event object.
	 */
	function handleClick(event) {
		// Get the target element
		const target = event.target;

		// Check if the target is the "invoiceAddRow" element
		if (target === invoiceAddRow) {
			// Call the generateRow function
			generateRow();
		}
		// Check if the target is the "invoiceRemoveRow" element and the serialNumber is greater than 2
		else if (target === invoiceRemoveRow && serialNumber > 2) {
			// Remove the last child element from the "invoiceListOfGoods" element
			invoiceListOfGoods.removeChild(invoiceListOfGoods.lastElementChild);

			// Decrease the serialNumber by 1
			serialNumber--;
		}
	}

	/**
	 * Handles the change event.
	 *
	 * @param {Event} event - The event object.
	 */
	function handleChange(event) {
		// Get the target element from the event object
		const target = event.target;

		// Check if the target element is the shippingInfoCheck checkbox
		if (target === shippingInfoCheck) {
			// Call the copyShippingInfo function if the shippingInfoCheck checkbox is checked
			copyShippingInfo();
		} else if (target === shippingAddressCheck) {
			// Call the copyShippingAddress function if the shippingAddressCheck checkbox is checked
			copyShippingAddress();
		}
	}

	/**
	 * Updates the amount based on the target element.
	 *
	 * @param {Object} target - The target element.
	 */
	function updateAmount(target) {
		// Extract the row ID from the target's ID
		const rowId = parseInt(target.id.match(/\d+/)[0]);

		// Get the quantity and rate elements for the corresponding row
		const qty = qtyElements[rowId].value;
		const rate = rateElements[rowId].value;

		// Calculate the amount if both quantity and rate are provided
		const amount = qty && rate ? (qty * rate).toFixed(2) : "";

		// Set the calculated amount on the corresponding element
		amountElements[rowId].value = amount;
	}

	/**
	 * Copies the shipping information to the billing information if the shipping information checkbox is checked. Otherwise, clears the billing information.
	 *
	 * @param {Array} shippingInfoArray - An array of shipping information elements.
	 * @param {Array} billingInfoArray - An array of billing information elements.
	 * @param {HTMLElement} shippingInfoCheck - The checkbox element for the shipping information.
	 */
	function copyShippingInfo(shippingInfoArray, billingInfoArray, shippingInfoCheck) {
		// Check if the shipping information checkbox is checked
		const isChecked = shippingInfoCheck.checked;

		// Loop through each element in the shippingInfoArray
		shippingInfoArray.forEach((info, i) => {
			// Copy the value from the shipping information to the billing information if the checkbox is checked
			// Otherwise, clear the value in the billing information
			info.value = isChecked ? billingInfoArray[i].value : "";
		});
	}

	/**
	 * Copies the shipping address to the billing address if the shipping address checkbox is checked.
	 * @param {Array} shippingAddressArray - The array of shipping address input elements.
	 * @param {Array} billingAddressArray - The array of billing address input elements.
	 * @param {HTMLInputElement} shippingAddressCheck - The checkbox element for the shipping address.
	 */
	function copyShippingAddress(shippingAddressArray, billingAddressArray, shippingAddressCheck) {
		// Check if the shipping address checkbox is checked
		const isChecked = shippingAddressCheck.checked;

		// Loop through each address input element in the shipping address array
		shippingAddressArray.forEach((address, i) => {
			// Copy the shipping address to the corresponding billing address if the checkbox is checked,
			// otherwise clear the billing address
			address.value = isChecked ? billingAddressArray[i].value : "";
		});
	}

	/**
	 * Updates the shipping information based on the provided billing info index.
	 *
	 * @param {number} billingInfoIndex - The index of the billing info to update.
	 */
	function updateShippingInfo(billingInfoIndex) {
		// Check if shipping info checkbox is checked
		if (shippingInfoCheck.checked) {
			// Update the value of shipping info with the value of billing info
			shippingInfoarray[billingInfoIndex].value = billingInfoarray[billingInfoIndex].value;
		}
	}

	/**
	 * Updates the shipping address based on the selected billing address.
	 *
	 * @param {number} billingAddressIndex - The index of the billing address to update the shipping address from.
	 */
	function updateShippingAddress(billingAddressIndex) {
		// Check if the shipping address checkbox is checked
		if (shippingAddressCheck.checked) {
			// Update the value of the shipping address with the value of the selected billing address
			shippingAddressarray[billingAddressIndex].value = billingAddressarray[billingAddressIndex].value;
		}
	}

	/**
	 * Updates the total amount based on the values of the amountElements.
	 */
	function updateTotalAmount() {
		// Initialize the total amount variable to 0
		let total = 0;

		// Iterate over each element in the amountElements array
		for (let element of amountElements) {
			// Check if the value of the element is not an empty string
			if (element.value !== "") {
				// Parse the value of the element and add it to the total amount
				total += parseFloat(element.value);
			}
		}

		// Set the value of the totalAmount element to the total amount
		totalAmount.value = total === 0 ? "" : total.toFixed(2);
	}

	/**
	 * Handles the form submission event.
	 *
	 * @param {Event} event - The form submission event.
	 * @return {void} This function does not return anything.
	 */
	async function handleSubmit(event) {
		// Prevent the default form submission behavior
		event.preventDefault();

		// Add the "was-validated" class to the form to trigger the validation styling
		invoiceForm.classList.add("was-validated");

		// Check if the form is valid
		if (!invoiceForm.checkValidity()) {
			return;
		}

		try {
			// Send a POST request to the current URL with the form data
			const response = await fetch(location.href, {
				method: "POST",
				body: new FormData(invoiceForm),
			});

			if (response.ok) {
				// Get the filename from the response headers
				const contentDisposition = response.headers.get("Content-Disposition");
				const filename = contentDisposition.match(/filename="(.+)"/)[1];

				// Create a File object from the response blob
				const blob = await response.blob();
				const file = new File([blob], filename);

				// Create a URL for the file and trigger a download
				const url = URL.createObjectURL(file);
				const a = document.createElement("a");
				a.href = url;
				a.download = filename;
				a.click();

				// Reload the current page
				location.replace(location.href);
			} else {
				console.error("Error:", response.status);

				// Get the error message from the response body
				let message = await response.text();
				message = encodeURIComponent(message);

				// Redirect to the apology page with the error message and status code
				const url = `/apology/${message}/${response.status}`;
				location.assign(url);
			}
		} catch (error) {
			console.error(error);

			// Show an error message to the user
			showErrorMessage(error);
		}
	}

	/**
	 * Displays an error message to the user.
	 *
	 * @param {TypeError} error - The error object that occurred.
	 * @return {undefined} This function does not return anything.
	 */
	function showErrorMessage(error) {
		// Determine the type of error and construct the appropriate alert message
		const alertMessage =
			error instanceof TypeError
				? `${error.message}. Check your Network connection and try again.`
				: `${error.message}. Please Contact Support.`;

		// Display the alert message to the user
		alert(alertMessage);
	}
});
