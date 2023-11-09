// When the DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
	// Get the form element
	const form = document.querySelector(".needs-validation");

	// Get the input elements
	const currentPassword = document.getElementById("current-password");
	const newPassword = document.getElementById("new-password");
	const confirmPassword = document.getElementById("confirm-password");

	// Add event listener for form submission
	form.addEventListener("submit", handleSubmit);

	// Add event listener for input changes
	form.addEventListener("input", handleInput);

	/**
	 * Handles form submission
	 * @param {Event} event - The form submission event
	 */
	function handleSubmit(event) {
		// Prevent form submission if it is invalid
		if (!form.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}

		// Check the validity of each input field
		checkInputValidity(currentPassword);
		checkInputValidity(newPassword);
		checkInputValidity(confirmPassword);
	}

	/**
	 * Handles the input event.
	 * @param {Event} event - The input event.
	 */
	function handleInput(event) {
		// Check if the target matches the new-password or confirm-password element
		if (event.target.matches("#new-password, #confirm-password")) {
			// Check the validity of the new password input
			checkInputValidity(newPassword);

			// Check the validity of the confirm password input
			checkInputValidity(confirmPassword);
		} else {
			// Check the validity of the event target
			checkInputValidity(event.target);
		}
	}

	/**
	 * Checks the validity of an input element and sets the appropriate validity classes.
	 * @param {HTMLInputElement} input - The input element to check.
	 */
	function checkInputValidity(input) {
		// Check if the input is valid
		const isValid = input.checkValidity();

		// Check if the input is the confirm password field
		if (input === confirmPassword) {
			// Check if the input is valid and the password matches
			if (isValid && checkPasswordMatch()) {
				// Set the validity classes to indicate a valid input
				setValidityClasses(input, true);
			} else {
				// Set the validity classes to indicate an invalid input
				setValidityClasses(input, false);
			}
		} else {
			// Set the validity classes based on the input's validity
			setValidityClasses(input, isValid);
		}
	}

	/**
	 * Checks if the new password matches the confirmed password.
	 * @returns {boolean} True if the passwords match, false otherwise.
	 */
	function checkPasswordMatch() {
		// Check if the confirmed password is empty
		if (confirmPassword.value === "") {
			return false;
		}

		// Check if the new password matches the confirmed password
		return newPassword.value === confirmPassword.value;
	}

	/**
	 * Sets the validity classes of an input element based on its validity state.
	 * @param {HTMLElement} input - The input element to set the validity classes on.
	 * @param {boolean} isValid - The validity state of the input element.
	 */
	function setValidityClasses(input, isValid) {
		// If the input is valid, remove the "is-invalid" class and add the "is-valid" class
		if (isValid) {
			input.classList.remove("is-invalid");
			input.classList.add("is-valid");
		}
		// If the input is not valid, remove the "is-valid" class and add the "is-invalid" class
		else {
			input.classList.remove("is-valid");
			input.classList.add("is-invalid");
		}
	}
});
