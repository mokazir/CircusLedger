document.addEventListener("DOMContentLoaded", () => {
	const form = document.querySelector(".needs-validation");
	const currentPassword = document.getElementById("current-password");
	const newPassword = document.getElementById("new-password");
	const confirmPassword = document.getElementById("confirm-password");

	form.addEventListener("submit", (event) => {
		if (!form.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}

		checkInputValidity(currentPassword);
		checkInputValidity(newPassword);
		checkInputValidity(confirmPassword);
	});

	form.addEventListener("input", (event) => {
		if (event.target.matches("#new-password, #confirm-password")) {
			checkInputValidity(newPassword);
			checkInputValidity(confirmPassword);
		} else {
			checkInputValidity(event.target);
		}
	});

	function checkInputValidity(input) {
		const isValid = input.checkValidity();
		if (input === confirmPassword) {
			if (isValid && checkPasswordMatch()) {
				setValidityClasses(input, true);
			} else {
				setValidityClasses(input, false);
			}
		} else {
			setValidityClasses(input, isValid);
		}
	}

	function checkPasswordMatch() {
		if (confirmPassword.value === "") {
			return false;
		}
		return newPassword.value === confirmPassword.value;
	}

	function setValidityClasses(input, isValid) {
		if (isValid) {
			input.classList.remove("is-invalid");
			input.classList.add("is-valid");
		} else {
			input.classList.remove("is-valid");
			input.classList.add("is-invalid");
		}
	}
});
