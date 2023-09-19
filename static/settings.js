document.addEventListener("DOMContentLoaded", () => {
	// Get references to DOM elements
	const inventory = document.getElementById("inventory");
	const inventoryNav = document.getElementById("inventory-nav");
	const goodsNav = inventoryNav.children[0];
	const clientsNav = inventoryNav.children[1];
	const goods = document.getElementById("goods");
	const clients = document.getElementById("clients");

	inventory.addEventListener("click", handleClick);

	function handleClick(event) {
		const target = event.target;
		if (target === goodsNav && !goodsNav.classList.contains("active")) {
			toggleActive(goodsNav, clientsNav, goods, clients);
		} else if (target === clientsNav && !clientsNav.classList.contains("active")) {
			toggleActive(clientsNav, goodsNav, clients, goods);
		}
	}

	function toggleActive(nav1, nav2, content1, content2) {
		nav2.classList.remove("active");
		nav2.removeAttribute("aria-current");
		content2.setAttribute("hidden", "");
		nav1.classList.add("active");
		nav1.setAttribute("aria-current", "page");
		content1.removeAttribute("hidden");
	}
});
