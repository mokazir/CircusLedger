// When the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
	// Get the form element
	const form = document.querySelector(".needs-validation");

	// Get the input elements
	const username = document.getElementById("username");
	const password = document.getElementById("password");
	const confirmPassword = document.getElementById("confirm-password");

	// Add event listener for form submission
	form.addEventListener("submit", handleSubmit);

	// Add event listener for input changes
	form.addEventListener("input", handleInput);

	/**
	 * Handle form submission
	 * @param {Event} event - The submit event
	 */
	function handleSubmit(event) {
		// Prevent form submission if it is not valid
		if (!form.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}

		// Check the validity of each input field
		checkInputValidity(username);
		checkInputValidity(password);
		checkInputValidity(confirmPassword);
	}

	/**
	 * Handle input changes
	 * @param {Event} event - The input event
	 */
	function handleInput(event) {
		// Check the validity of password and confirm password fields
		if (event.target.matches("#password, #confirm-password")) {
			// Check input validity for password field
			checkInputValidity(password);
			// Check input validity for confirm password field
			checkInputValidity(confirmPassword);
		} else {
			// Check the validity of the current input field
			checkInputValidity(event.target);
		}
	}

	/**
	 * Check the validity of an input field
	 * @param {HTMLElement} input - The input field to check
	 */
	function checkInputValidity(input) {
		// Check if the input field is valid
		const isValid = input.checkValidity();

		// If the input field is the confirm password field
		if (input === confirmPassword) {
			// Check if the confirm password matches the password
			if (isValid && checkPasswordMatch()) {
				// Set validity classes to indicate a valid input
				setValidityClasses(input, true);
			} else {
				// Set validity classes to indicate an invalid input
				setValidityClasses(input, false);
			}
		} else {
			// Set the validity classes based on the input validity
			setValidityClasses(input, isValid);
		}
	}

	/**
	 * Check if the password matches the confirm password
	 *
	 * @returns {boolean} - True if the passwords match, false otherwise
	 */
	function checkPasswordMatch() {
		// Check if the confirm password is empty
		if (confirmPassword.value === "") {
			return false;
		}

		// Check if the password and confirm password match
		return password.value === confirmPassword.value;
	}

	/**
	 * Set the validity classes for an input field
	 * @param {HTMLElement} input - The input field
	 * @param {boolean} isValid - Flag indicating the validity of the input field
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
