const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const cards = [...document.querySelectorAll("[data-preview]")];

function animateCard(card) {
  card.classList.add("is-visible");
  if (reduceMotion.matches || !card.animate) return;
  card.animate(
    [
      { opacity: 0, transform: "translateY(24px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    {
      duration: 260,
      easing: "cubic-bezier(0.23, 1, 0.32, 1)"
    }
  );
}

function revealCards() {
  if (reduceMotion.matches || !("IntersectionObserver" in window)) {
    cards.forEach(animateCard);
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateCard(entry.target);
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12 }
  );

  cards.forEach((card) => observer.observe(card));
}

function enablePointerResponse() {
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  if (reduceMotion.matches || !finePointer.matches) return;

  cards.forEach((card) => {
    const stage = card.querySelector(".preview-stage");
    if (!stage) return;

    card.addEventListener("pointermove", (event) => {
      const bounds = card.getBoundingClientRect();
      const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 12;
      const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 12;
      stage.style.setProperty("--pointer-x", `${x.toFixed(2)}px`);
      stage.style.setProperty("--pointer-y", `${y.toFixed(2)}px`);
    });

    card.addEventListener("pointerleave", () => {
      stage.style.setProperty("--pointer-x", "0px");
      stage.style.setProperty("--pointer-y", "0px");
    });
  });
}

revealCards();
enablePointerResponse();
