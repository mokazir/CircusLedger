// When the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
	let serialNumber = 1;

	// Get references to DOM elements (statically generated)
	const quoteForm = document.getElementById("quote-form");
	const quoteListOfGoods = document.getElementById("quote-list-of-goods");
	const totalAmount = document.getElementById("total-amount");
	const quoteAddRow = document.getElementById("quote-add-row");
	const quoteRemoveRow = document.getElementById("quote-remove-row");

	// Cache frequently accessed elements
	const qtyElements = [];
	const rateElements = [];
	const amountElements = [];

	// Event listener for input changes
	quoteForm.addEventListener("input", handleInput);

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
		// Generate the HTML for the new row
		const rowHTML = `
		<div class="pb-md-1" id="quote${serialNumber}">
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
							id="serialNumber${serialNumber}"
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
	function handleInput(event) {
		// Get the target element of the event
		const target = event.target;

		// Check if the target element has an id that starts with 'qty' or 'rate'
		if (target.matches("[id^='qty']") || target.matches("[id^='rate']")) {
			// Update the amount based on the target element
			updateAmount(target);

			// Update the total amount
			updateTotalAmount();
		}
	}

	/**
	 * Handles the click event.
	 *
	 * @param {Event} event - The click event object.
	 */
	function handleClick(event) {
		// Get the target element of the click event
		const target = event.target;

		// Check if the target is the "quoteAddRow" element
		if (target === quoteAddRow) {
			// Call the "generateRow" function to generate a new row
			generateRow();
		}
		// Check if the target is the "quoteRemoveRow" element and if the serialNumber is greater than 2
		else if (target === quoteRemoveRow && serialNumber > 2) {
			// Remove the last child element from the "quoteListOfGoods" element
			quoteListOfGoods.removeChild(quoteListOfGoods.lastElementChild);
			// Decrease the serialNumber by 1
			serialNumber--;
		}
	}

	/**
	 * Updates the amount based on the target element.
	 *
	 * @param {Object} target - The target element.
	 */
	function updateAmount(target) {
		// Extract the row ID from the target element's ID
		const rowId = parseInt(target.id.match(/\d+/)[0]);

		// Get the current quantity and rate values from the corresponding row elements
		const qty = qtyElements[rowId].value;
		const rate = rateElements[rowId].value;

		// Calculate the amount based on the quantity and rate values
		const amount = qty && rate ? (qty * rate).toFixed(2) : "";

		// Update the amount element with the calculated amount
		amountElements[rowId].value = amount;
	}

	/**
	 * Updates the total amount based on the values of the amountElements.
	 *
	 * @param {type} paramName - description of parameter
	 * @return {type} description of return value
	 */
	function updateTotalAmount() {
		// Calculate the total amount by summing up the values of the amountElements
		const total = amountElements.reduce(
			// Convert the value to a float if it is not an empty string,
			// otherwise, treat it as 0
			(acc, element) => acc + (element.value !== "" ? parseFloat(element.value) : 0),
			0
		);

		// Set the value of totalAmount to the total amount,
		// formatted with two decimal places
		totalAmount.value = total === 0 ? "" : total.toFixed(2);
	}

	/**
	 * Handles the form submission event.
	 *
	 * @param {Event} event - The form submission event.
	 * @return {Promise} A Promise that resolves when the form submission is completed.
	 */
	async function handleSubmit(event) {
		// Prevent the default form submission behavior
		event.preventDefault();

		// Add the "was-validated" class to the form to trigger the validation styling
		quoteForm.classList.add("was-validated");

		// Check if the form is valid
		if (!quoteForm.checkValidity()) {
			return;
		}

		try {
			// Send a POST request to the current URL with the form data
			const response = await fetch(location.href, {
				method: "POST",
				body: new FormData(quoteForm),
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
	 * Display an error message based on the given error.
	 * @param {Error} error - The error object.
	 */
	function showErrorMessage(error) {
		// Determine the appropriate alert message based on the error type
		const alertMessage =
			error instanceof TypeError
				? `${error.message}. Check your Network connection and try again.`
				: `${error.message}. Please Contact Support.`;

		// Show the alert message
		alert(alertMessage);
	}
});
