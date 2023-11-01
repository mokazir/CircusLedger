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
							id="serialNumber${serialNumber}"
							placeholder="S.No"
							value="${serialNumber}"
							readonly />
					</div>
				</div>
				<div class="col-md">
					<input class="form-control" type="text" name="descp" placeholder="Description of goods" required />
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
	function handleInput(event) {
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
	 * Handles the form submission event.
	 *
	 * @param {Event} event - The form submission event.
	 * @return {Promise} A Promise that resolves when the form submission is completed.
	 */
	async function handleSubmit(event) {
		event.preventDefault();

		quoteForm.classList.add("was-validated");
		if (!quoteForm.checkValidity()) {
			return;
		}

		try {
			const response = await fetch(location.href, {
				method: "POST",
				body: new FormData(quoteForm),
			});
			if (response.ok) {
				const contentDisposition = response.headers.get("Content-Disposition");
				const filename = contentDisposition.match(/filename="(.+)"/)[1];
				const blob = await response.blob();
				const file = new File([blob], filename);
				const url = URL.createObjectURL(file);
				const a = document.createElement("a");
				a.href = url;
				a.download = filename;
				a.click();
				location.replace(location.href);
			} else {
				console.error("Error:", response.status);
				let message = await response.text();
				message = encodeURIComponent(message);
				const url = `/apology/${message}/${response.status}`;
				location.assign(url);
			}
		} catch (error) {
			console.error(error);
			showErrorMessage(error);
		}
	}

	function showErrorMessage(error) {
		const alertMessage =
			error instanceof TypeError
				? `${error.message}. Check your Network connection and try again.`
				: `${error.message}. Please Contact Support.`;

		alert(alertMessage);
	}
});
