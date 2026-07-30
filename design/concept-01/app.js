const root = document.documentElement;
const lab = document.querySelector(".mechanism-lab");
const pressureInput = document.querySelector("#pressure");
const pressureOutput = document.querySelector("#pressure-state");
const probeButtons = [...document.querySelectorAll("[data-probe]")].filter(
  (button) => button.tagName === "BUTTON"
);
const resetButton = document.querySelector("#reset-mechanism");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function animateReveal(item) {
  item.classList.add("is-visible");
  if (reduceMotion.matches || !item.animate) return;
  item.animate(
    [
      { opacity: 0, transform: "translateY(20px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    {
      duration: 260,
      easing: "cubic-bezier(0.23, 1, 0.32, 1)"
    }
  );
}

function renderPressure(value) {
  const pressure = Math.min(Math.max(Number(value) / 100, 0), 1);
  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--contact-width", `${18 + pressure * 62}%`);
  pressureOutput.value =
    pressure < 0.08
      ? "Air gap"
      : pressure < 0.55
        ? "Partial coupling"
        : "Expanded coupling";
}

function selectProbe(probe) {
  lab.dataset.probe = probe;
  probeButtons.forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.probe === probe)
    );
  });
}

function revealContent() {
  const items = [...document.querySelectorAll("[data-reveal]")];
  if (reduceMotion.matches || !("IntersectionObserver" in window)) {
    items.forEach(animateReveal);
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateReveal(entry.target);
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
  );

  items.forEach((item) => observer.observe(item));
}

pressureInput.addEventListener("input", (event) => {
  renderPressure(event.currentTarget.value);
});

probeButtons.forEach((button) => {
  button.addEventListener("click", () => selectProbe(button.dataset.probe));
});

resetButton.addEventListener("click", () => {
  pressureInput.value = "0";
  selectProbe("sphere");
  renderPressure(0);
  pressureInput.focus();
});

renderPressure(pressureInput.value);
revealContent();
