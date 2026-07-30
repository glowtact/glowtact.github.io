const root = document.documentElement;
const workbench = document.querySelector(".specimen-workbench");
const lensInput = document.querySelector("#lens-position");
const lensOutput = document.querySelector("#lens-output");
const layerTitle = document.querySelector("#layer-title");
const layerDescription = document.querySelector("#layer-description");
const layerButtons = [...document.querySelectorAll("[data-layer]")].filter(
  (element) => element.tagName === "BUTTON"
);
const specimenButtons = [...document.querySelectorAll("[data-specimen]")];
const specimenImage = document.querySelector("#specimen-image");
const specimenTitle = document.querySelector("#specimen-title");
const specimenNote = document.querySelector("#specimen-note");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function animateReveal(item) {
  item.classList.add("is-visible");
  if (reduceMotion.matches || !item.animate) return;
  item.animate(
    [
      { opacity: 0, transform: "translateY(18px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    {
      duration: 260,
      easing: "cubic-bezier(0.23, 1, 0.32, 1)"
    }
  );
}

const layers = Object.freeze({
  membrane: {
    title: "Membrane geometry",
    description:
      "The unbonded black elastomer membrane sits above the microtextured transparent gel."
  },
  coupling: {
    title: "Optical coupling",
    description:
      "The amber region marks where pressure increases local membrane–gel optical coupling."
  },
  tactile: {
    title: "Tactile output",
    description:
      "Reduced local reflection and absorption by the black membrane produce a darker tactile region."
  }
});

const specimens = Object.freeze({
  thread: {
    image: "../assets/images/thread-mesh.png",
    alt: "Qualitative reconstruction of M1 screw threads",
    title: "M1 screw threads",
    note: "Fine repeated geometry remains spatially legible."
  },
  phillips: {
    image: "../assets/images/phillips-mesh.png",
    alt: "Qualitative reconstruction of a Phillips screw head",
    title: "Phillips head",
    note: "A recessed cross profile appears in the qualitative reconstruction."
  },
  balls: {
    image: "../assets/images/ball-array-mesh.png",
    alt: "Qualitative reconstruction of a separated ball array",
    title: "Calibration ball array",
    note: "Separated circular contacts preserve their spatial arrangement."
  }
});

function renderLens(value) {
  const position = Math.min(Math.max(Number(value), 0), 100);
  root.style.setProperty("--lens-position", `${position}%`);
  lensOutput.value = `${Math.round(position)}%`;
}

function selectLayer(layer) {
  const content = layers[layer];
  if (!content) return;
  workbench.dataset.layer = layer;
  layerTitle.textContent = content.title;
  layerDescription.textContent = content.description;
  layerButtons.forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.layer === layer)
    );
  });
}

function selectSpecimen(key) {
  const specimen = specimens[key];
  if (!specimen) return;
  specimenImage.src = specimen.image;
  specimenImage.alt = specimen.alt;
  specimenTitle.textContent = specimen.title;
  specimenNote.textContent = specimen.note;
  specimenButtons.forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.specimen === key)
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
    { threshold: 0.1, rootMargin: "0px 0px -5% 0px" }
  );

  items.forEach((item) => observer.observe(item));
}

lensInput.addEventListener("input", (event) => {
  renderLens(event.currentTarget.value);
});

layerButtons.forEach((button) => {
  button.addEventListener("click", () => selectLayer(button.dataset.layer));
});

specimenButtons.forEach((button) => {
  button.addEventListener("click", () =>
    selectSpecimen(button.dataset.specimen)
  );
});

renderLens(lensInput.value);
selectLayer("coupling");
selectSpecimen("thread");
revealContent();
