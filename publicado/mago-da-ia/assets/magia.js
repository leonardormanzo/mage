const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

window.requestAnimationFrame(() => {
  window.scrollTo({ left: 0, top: window.scrollY, behavior: "auto" });
});

if (reduceMotion) {
  document.querySelectorAll(".brand-animation").forEach((video) => {
    video.pause();
    video.removeAttribute("autoplay");
  });
}

const magicTrigger = document.querySelector("#make-magic");
const transition = document.querySelector(".portal-transition");

if (magicTrigger && transition) {
  magicTrigger.addEventListener("click", (event) => {
    if (reduceMotion || event.metaKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    const rect = magicTrigger.getBoundingClientRect();
    transition.style.setProperty("--transition-x", `${rect.left + rect.width / 2}px`);
    transition.style.setProperty("--transition-y", `${rect.top + rect.height / 2}px`);
    transition.classList.add("active");
    window.setTimeout(() => { window.location.href = magicTrigger.href; }, 780);
  });
}

const revealItems = document.querySelectorAll(".reveal");
if (revealItems.length) {
  if (reduceMotion) {
    revealItems.forEach((item) => item.classList.add("visible"));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
    revealItems.forEach((item) => observer.observe(item));
  }
}

const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#experience-nav");
if (menuButton && navigation) {
  menuButton.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!open));
    navigation.classList.toggle("open", !open);
  });
  navigation.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menuButton.setAttribute("aria-expanded", "false");
      navigation.classList.remove("open");
    });
  });
}

const parallaxItems = [...document.querySelectorAll("[data-parallax]")];
const root = document.documentElement;
let pointerX = 0;
let pointerY = 0;
let scrollY = window.scrollY;
let frameRequested = false;

function paintMotion() {
  root.style.setProperty("--cursor-x", `${pointerX}px`);
  root.style.setProperty("--cursor-y", `${pointerY}px`);
  const documentHeight = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
  root.style.setProperty("--scroll-progress", `${Math.min(100, (scrollY / documentHeight) * 100)}%`);
  parallaxItems.forEach((item) => {
    const depth = Number(item.dataset.parallax || 0);
    item.style.setProperty("--depth", depth);
    item.style.setProperty("--mouse-x", `${(pointerX - window.innerWidth / 2) * 0.025}px`);
    item.style.setProperty("--mouse-y", `${(pointerY - window.innerHeight / 2) * 0.025}px`);
    item.style.setProperty("--scroll-y", `${scrollY * -0.045}px`);
  });
  frameRequested = false;
}

function requestPaint() {
  if (!frameRequested && !reduceMotion) {
    frameRequested = true;
    window.requestAnimationFrame(paintMotion);
  }
}

if (!reduceMotion && parallaxItems.length) {
  window.addEventListener("pointermove", (event) => {
    pointerX = event.clientX;
    pointerY = event.clientY;
    requestPaint();
  }, { passive: true });
  window.addEventListener("scroll", () => {
    scrollY = window.scrollY;
    requestPaint();
  }, { passive: true });
  pointerX = window.innerWidth * .65;
  pointerY = window.innerHeight * .3;
  paintMotion();
}

document.querySelectorAll(".fx-button").forEach((button) => {
  if (reduceMotion) return;
  button.addEventListener("pointermove", (event) => {
    const rect = button.getBoundingClientRect();
    const x = event.clientX - rect.left - rect.width / 2;
    const y = event.clientY - rect.top - rect.height / 2;
    button.style.transform = `translate(${x * .06}px, ${y * .09 - 4}px)`;
  });
  button.addEventListener("pointerleave", () => {
    button.style.transform = "";
  });
});
