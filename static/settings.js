// document.addEventListener("DOMContentLoaded", () => {
// 	// Get references to DOM elements
// 	const settings = document.getElementById("settings");
// 	const settingsNav = document.getElementById("settings-nav");
// 	const userNav = settingsNav.children[0];
// 	const companyNav = settingsNav.children[1];
// 	const user = document.getElementById("user");
// 	const company = document.getElementById("company");

// 	settings.addEventListener("click", handleClick);

// 	/**
// 	 * Handles the click event.
// 	 *
// 	 * @param {Event} event - The event object.
// 	 */
// 	function handleClick(event) {
// 		const target = event.target;
// 		if (target === userNav && !userNav.classList.contains("active")) {
// 			toggleActive(userNav, companyNav, user, company);
// 		} else if (target === companyNav && !companyNav.classList.contains("active")) {
// 			toggleActive(companyNav, userNav, company, user);
// 		}
// 	}

// 	/**
// 	 * Toggles the active state of two navigation elements and their corresponding content.
// 	 *
// 	 * @param {HTMLElement} nav1 - The first navigation element to toggle.
// 	 * @param {HTMLElement} nav2 - The second navigation element to toggle.
// 	 * @param {HTMLElement} content1 - The first content element to toggle.
// 	 * @param {HTMLElement} content2 - The second content element to toggle.
// 	 */
// 	function toggleActive(nav1, nav2, content1, content2) {
// 		nav2.classList.remove("active");
// 		nav2.removeAttribute("aria-current");
// 		content2.setAttribute("hidden", "");
// 		nav1.classList.add("active");
// 		nav1.setAttribute("aria-current", "page");
// 		content1.removeAttribute("hidden");
// 	}
// });
