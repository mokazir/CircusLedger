(() => {
	"use strict";

	// Get the form element with the class "needs-validation"
	const form = document.querySelector(".needs-validation");

	// Add event listener for the form's submit event
	form.addEventListener(
		"submit",
		(event) => {
			// Check if the form is valid
			if (!form.checkValidity()) {
				// Prevent form submission if it's not valid
				event.preventDefault();
				event.stopPropagation();
			}

			// Add the "was-validated" class to the form to show validation feedback
			form.classList.add("was-validated");
		},
		false
	);
})();
