// Wait for the DOM to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
	// Find the element with the 'active' class
	const active = document.querySelector(".active");

	// Set the 'aria-current' attribute to 'page' if the element exists
	active?.setAttribute("aria-current", "page");
});
