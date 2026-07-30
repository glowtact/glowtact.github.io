const root = document.documentElement;
const pressureInput = document.querySelector("#signal-pressure");
const pressurePercent = document.querySelector("#pressure-percent");
const toolbarState = document.querySelector("#toolbar-state");
const interfaceReadout = document.querySelector("#readout-interface");
const reflectionReadout = document.querySelector("#readout-reflection");
const outputReadout = document.querySelector("#readout-output");
const playButton = document.querySelector("#play-sequence");
const playLabel = document.querySelector("#play-label");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

let frame = 0;
let startedAt = 0;
let isPlaying = false;

function animateReveal(item) {
  item.classList.add("is-visible");
  if (reduceMotion.matches || !item.animate) return;
  item.animate(
    [
      { opacity: 0, transform: "translateY(16px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    {
      duration: 240,
      easing: "cubic-bezier(0.23, 1, 0.32, 1)"
    }
  );
}

function stateFor(pressure) {
  if (pressure < 0.08) {
    return {
      interface: "Air gap",
      reflection: "Diffuse reflection",
      output: "Light-gray field"
    };
  }
  if (pressure < 0.55) {
    return {
      interface: "Partial coupling",
      reflection: "Reduced locally",
      output: "Darkening region"
    };
  }
  return {
    interface: "Expanded coupling",
    reflection: "Further reduced",
    output: "Larger dark region"
  };
}

function render(value) {
  const pressure = Math.min(Math.max(Number(value), 0), 1);
  const percent = Math.round(pressure * 100);
  const state = stateFor(pressure);

  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--signal-level", `${percent}%`);
  pressureInput.value = String(percent);
  pressurePercent.value = `${percent}%`;
  toolbarState.value = state.interface;
  interfaceReadout.textContent = state.interface;
  reflectionReadout.textContent = state.reflection;
  outputReadout.textContent = state.output;
}

function stopPlayback() {
  isPlaying = false;
  startedAt = 0;
  cancelAnimationFrame(frame);
  playButton.setAttribute("aria-pressed", "false");
  playLabel.textContent = "Run once";
}

function tick(now) {
  if (!startedAt) startedAt = now;
  const progress = Math.min((now - startedAt) / 2200, 1);
  render(progress);
  if (progress < 1 && isPlaying) {
    frame = requestAnimationFrame(tick);
  } else {
    stopPlayback();
  }
}

function startPlayback() {
  if (reduceMotion.matches) {
    render(1);
    stopPlayback();
    return;
  }
  isPlaying = true;
  startedAt = 0;
  playButton.setAttribute("aria-pressed", "true");
  playLabel.textContent = "Pause";
  render(0);
  frame = requestAnimationFrame(tick);
}

function togglePlayback() {
  if (isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
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

playButton.addEventListener("click", togglePlayback);

pressureInput.addEventListener("input", (event) => {
  stopPlayback();
  render(Number(event.currentTarget.value) / 100);
});

pressureInput.addEventListener("pointerdown", stopPlayback);
pressureInput.addEventListener("keydown", stopPlayback);

render(Number(pressureInput.value) / 100);
revealContent();
