// document.addEventListener("DOMContentLoaded", () => {
// 	// Get references to DOM elements
// 	const inventory = document.getElementById("inventory");
// 	const inventoryNav = document.getElementById("inventory-nav");
// 	const goodsNav = inventoryNav.children[0];
// 	const clientsNav = inventoryNav.children[1];
// 	const goods = document.getElementById("goods");
// 	const clients = document.getElementById("clients");

// 	inventory.addEventListener("click", handleClick);

// 	function handleClick(event) {
// 		const target = event.target;
// 		if (target === goodsNav && !goodsNav.classList.contains("active")) {
// 			toggleActive(goodsNav, clientsNav, goods, clients);
// 		} else if (target === clientsNav && !clientsNav.classList.contains("active")) {
// 			toggleActive(clientsNav, goodsNav, clients, goods);
// 		}
// 	}

// 	function toggleActive(nav1, nav2, content1, content2) {
// 		nav2.classList.remove("active");
// 		nav2.removeAttribute("aria-current");
// 		content2.setAttribute("hidden", "");
// 		nav1.classList.add("active");
// 		nav1.setAttribute("aria-current", "page");
// 		content1.removeAttribute("hidden");
// 	}

// 	// function generateSerialNumbers() {
// 	// 	const table = document.getElementById("clients"); // Get the table element
// 	// 	const rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr"); // Get all the table rows in the tbody

// 	// 	Array.from(rows).forEach((row, index) => {
// 	// 		// Use Array.from() to convert the HTMLCollection to an array and iterate over each row
// 	// 		let serialNumberCell = row.getElementsByTagName("th")[0]; // Get the first td element in the current row
// 	// 		serialNumberCell.textContent = index + 1; // Set the serial number
// 	// 	});
// 	// }

// 	// // Call the function to generate serial numbers when the page loads
// 	// generateSerialNumbers();

// 	// function generateSerialNumbers() {
// 	// 	const updateSerialNumbers = (rows) => {
// 	// 		rows.forEach((row, index) => {
// 	// 			row.querySelector("th").textContent = index + 1;
// 	// 		});
// 	// 	};

// 	// 	const goodsrows = document.querySelectorAll("#goods tbody tr");
// 	// 	const clientsrows = document.querySelectorAll("#clients tbody tr");

// 	// 	updateSerialNumbers(goodsrows);
// 	// 	updateSerialNumbers(clientsrows);
// 	// }

// 	// // Call the function to generate serial numbers when the page loads
// 	// generateSerialNumbers();
// });
