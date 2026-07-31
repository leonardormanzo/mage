const menuButton = document.querySelector("[data-menu]");
const navLinks = document.querySelector("[data-nav]");

if (menuButton && navLinks) {
  menuButton.addEventListener("click", () => {
    const open = navLinks.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", String(open));
  });
}

document.querySelectorAll("[data-year]").forEach((node) => {
  node.textContent = new Date().getFullYear();
});
