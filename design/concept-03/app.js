const root = document.documentElement;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const pressureInput = document.querySelector("#signal-pressure");
const pressurePercent = document.querySelector("#pressure-percent");
const toolbarState = document.querySelector("#toolbar-state");
const playButton = document.querySelector("#play-sequence");
const playLabel = document.querySelector("#play-label");
const stateIndex = document.querySelector("#state-index");
const stateCopy = document.querySelector("#state-copy");
const stateItems = [...document.querySelectorAll(".state-rail li")];
const contactFraction = document.querySelector("#contact-fraction");
const cameraIntensity = document.querySelector("#camera-intensity");

const microTabs = [...document.querySelectorAll('[role="tab"][aria-controls]')];
const microPanels = [...document.querySelectorAll('[role="tabpanel"]')];
const microCanvas = document.querySelector("#micro-canvas");
const microContext = microCanvas?.getContext("2d") ?? null;
const canvasFallback = document.querySelector(".canvas-fallback");

const macroGel = document.querySelector(".macro-gel");
const macroTextureLine = document.querySelector(".macro-texture-line");
const macroMembrane = document.querySelector("#macro-membrane");
const macroMembraneShadow = document.querySelector("#macro-membrane-shadow");
const macroAirGap = document.querySelector("#macro-air-gap");
const macroCouplingLine = document.querySelector("#macro-coupling-line");
const macroCouplingGlow = document.querySelector("#macro-coupling-glow");
const macroFieldOfView = document.querySelector("#macro-field-of-view");
const macroCameraAperture = document.querySelector(".macro-camera-aperture");

const microSurfaceFill = document.querySelector("#micro-surface-fill");
const microSurfaceLine = document.querySelector("#micro-surface-line");
const microMembrane = document.querySelector("#micro-membrane");
const microMembraneShadow = document.querySelector("#micro-membrane-shadow");
const microGapArea = document.querySelector("#micro-gap-area");
const microContactPoints = document.querySelector("#micro-contact-points");

const FIELD_SIZE = 29;
const FIELD_SEED = 2500;
const SVG_NS = "http://www.w3.org/2000/svg";

let activeMicroView = "2d";
let currentPressure = Number(pressureInput?.value ?? 32) / 100;
let isPlaying = false;
let startedAt = 0;
let frame = 0;

function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function generateSurfaceField(size, seed) {
  const random = seededRandom(seed);
  const components = Array.from({ length: 11 }, (_, index) => {
    const band = index < 3 ? 1 : index < 7 ? 2 : 3;
    const angle = random() * Math.PI * 2;
    const frequency = band * (0.72 + random() * 0.78);
    return {
      x: Math.cos(angle) * frequency,
      y: Math.sin(angle) * frequency,
      phase: random() * Math.PI * 2,
      amplitude: 1 / Math.pow(frequency, 1.36)
    };
  });

  const grains = Array.from({ length: 18 }, () => ({
    x: random(),
    y: random(),
    radius: 0.035 + random() * 0.075,
    height: (random() - 0.32) * 0.65
  }));

  const values = [];
  let minimum = Infinity;
  let maximum = -Infinity;

  for (let row = 0; row < size; row += 1) {
    const line = [];
    for (let column = 0; column < size; column += 1) {
      const x = column / (size - 1);
      const y = row / (size - 1);
      let height = 0;

      components.forEach((component) => {
        const wave =
          (x * component.x + y * component.y) * Math.PI * 2 + component.phase;
        height += Math.sin(wave) * component.amplitude;
        height += Math.cos(wave * 0.51 + component.phase * 0.38) * component.amplitude * 0.26;
      });

      grains.forEach((grain) => {
        const dx = x - grain.x;
        const dy = y - grain.y;
        const distance = (dx * dx + dy * dy) / (grain.radius * grain.radius);
        height += Math.exp(-distance * 2.4) * grain.height;
      });

      line.push(height);
      minimum = Math.min(minimum, height);
      maximum = Math.max(maximum, height);
    }
    values.push(line);
  }

  const range = Math.max(maximum - minimum, Number.EPSILON);
  return values.map((line) =>
    line.map((height) => Math.pow((height - minimum) / range, 0.92))
  );
}

const surfaceField = generateSurfaceField(FIELD_SIZE, FIELD_SEED);
const surfaceSlice = surfaceField[Math.floor(FIELD_SIZE * 0.53)];

function stateFor(pressure) {
  if (pressure < 0.1) {
    return {
      key: "gap",
      index: "STATE 00",
      title: "Air gap",
      reflection: "Diffuse reflection",
      intensity: "Light-gray field",
      copy:
        "The taut membrane rests near the highest asperities. Microscopic air gaps preserve the reflective gel–air interface."
    };
  }

  if (pressure < 0.58) {
    return {
      key: "local",
      index: "STATE 01",
      title: "Local coupling",
      reflection: "Reduced locally",
      intensity: "Reduced",
      copy:
        "Pressure closes local gaps. The black membrane begins to absorb light where it optically couples to the gel."
    };
  }

  return {
    key: "expanded",
    index: "STATE 02",
    title: "Expanded coupling",
    reflection: "Further reduced",
    intensity: "Dark region",
    copy:
      "More asperities enter contact and neighboring contact islands connect. The absorbing region becomes larger and darker."
  };
}

function contactThreshold(pressure) {
  return 1.015 - pressure * 0.78;
}

function contactRatio(pressure) {
  const threshold = contactThreshold(pressure);
  let count = 0;
  let total = 0;
  surfaceField.forEach((row) => {
    row.forEach((height) => {
      total += 1;
      if (height >= threshold) count += 1;
    });
  });
  return total ? count / total : 0;
}

function smoothPath(points) {
  if (!points.length) return "";
  if (points.length === 1) return `M${points[0].x} ${points[0].y}`;

  let path = `M${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  for (let index = 1; index < points.length - 1; index += 1) {
    const point = points[index];
    const next = points[index + 1];
    const midpointX = (point.x + next.x) / 2;
    const midpointY = (point.y + next.y) / 2;
    path += ` Q${point.x.toFixed(2)} ${point.y.toFixed(2)} ${midpointX.toFixed(2)} ${midpointY.toFixed(2)}`;
  }

  const penultimate = points[points.length - 2];
  const last = points[points.length - 1];
  path += ` Q${penultimate.x.toFixed(2)} ${penultimate.y.toFixed(2)} ${last.x.toFixed(2)} ${last.y.toFixed(2)}`;
  return path;
}

function areaBetween(topPoints, bottomPoints) {
  if (!topPoints.length || !bottomPoints.length) return "";
  const topPath = smoothPath(topPoints);
  const bottom = [...bottomPoints].reverse();
  return `${topPath} L${bottom[0].x.toFixed(2)} ${bottom[0].y.toFixed(2)} ${bottom
    .slice(1)
    .map((point) => `L${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ")} Z`;
}

function macroSurfaceY(x) {
  return 286 + Math.sin(x * 0.061) * 0.9 + Math.sin(x * 0.127 + 0.8) * 0.45;
}

function macroIndentationWeight(x) {
  return Math.exp(-Math.pow((x - 460) / 180, 4));
}

function renderMacro(pressure) {
  if (!macroMembrane || !macroGel) return;

  const surfacePoints = [];
  const membranePoints = [];
  const start = 70;
  const end = 850;
  const samples = 65;

  for (let index = 0; index < samples; index += 1) {
    const x = start + (index / (samples - 1)) * (end - start);
    const indentation = macroIndentationWeight(x);
    const surfaceY = macroSurfaceY(x);
    const desiredMembraneY = 254 + indentation * pressure * 78;
    const membraneY = Math.min(desiredMembraneY, surfaceY - 4);

    surfacePoints.push({ x, y: surfaceY });
    membranePoints.push({ x, y: membraneY });
  }

  const surfacePath = smoothPath(surfacePoints);
  const gelPath = `${surfacePath} L850 448 L70 448 Z`;
  const membranePath = smoothPath(membranePoints);
  const gapPath = areaBetween(membranePoints, surfacePoints);

  macroGel.setAttribute("d", gelPath);
  macroTextureLine?.setAttribute("d", surfacePath);
  macroMembrane.setAttribute("d", membranePath);
  macroMembraneShadow?.setAttribute("d", membranePath);
  macroAirGap?.setAttribute("d", gapPath);

  const centerIndex = Math.floor(samples / 2);
  let coupledStart = centerIndex;
  let coupledEnd = centerIndex;
  const isCoupled = (index) =>
    surfacePoints[index].y - membranePoints[index].y <= 5.2;
  if (isCoupled(centerIndex)) {
    while (coupledStart > 0 && isCoupled(coupledStart - 1)) coupledStart -= 1;
    while (coupledEnd < samples - 1 && isCoupled(coupledEnd + 1)) coupledEnd += 1;
  }
  const coupled = isCoupled(centerIndex)
    ? surfacePoints.slice(coupledStart, coupledEnd + 1)
    : [];
  macroCouplingLine?.setAttribute("d", coupled.length > 1 ? smoothPath(coupled) : "");

  const ratio = contactRatio(pressure);
  macroCouplingGlow?.setAttribute("rx", String(32 + ratio * 230));
  macroCouplingGlow?.setAttribute("ry", String(14 + ratio * 36));
  macroFieldOfView?.setAttribute("opacity", (0.22 + ratio * 0.72).toFixed(3));
  macroCameraAperture?.setAttribute("opacity", (0.48 + ratio * 0.52).toFixed(3));
}

function renderMicro2D(pressure) {
  if (!microSurfaceFill || !microMembrane) return;

  const surfacePoints = surfaceSlice.map((height, index) => ({
    x: 28 + (index / (surfaceSlice.length - 1)) * 464,
    y: 236 - height * 88
  }));
  const threshold = contactThreshold(pressure);
  const desiredY = 236 - threshold * 88;
  const membranePoints = surfacePoints.map((point, index) => {
    const xNormal = index / (surfacePoints.length - 1);
    const edgeLift = Math.pow(Math.abs(xNormal - 0.5) * 2, 4) * 7;
    return {
      x: point.x,
      y: Math.min(desiredY - edgeLift, point.y - 3)
    };
  });

  const surfacePath = smoothPath(surfacePoints);
  const membranePath = smoothPath(membranePoints);
  microSurfaceFill.setAttribute("d", `${surfacePath} L492 300 L28 300 Z`);
  microSurfaceLine?.setAttribute("d", surfacePath);
  microMembrane.setAttribute("d", membranePath);
  microMembraneShadow?.setAttribute("d", membranePath);
  microGapArea?.setAttribute("d", areaBetween(membranePoints, surfacePoints));

  if (!microContactPoints) return;
  microContactPoints.replaceChildren();
  surfacePoints.forEach((point, index) => {
    if (surfaceSlice[index] < threshold) return;
    const contact = document.createElementNS(SVG_NS, "circle");
    contact.setAttribute("cx", point.x.toFixed(2));
    contact.setAttribute("cy", (point.y - 1).toFixed(2));
    contact.setAttribute("r", String(2.2 + pressure * 2.4));
    microContactPoints.append(contact);
  });
}

function resizeCanvas() {
  if (!microCanvas || !microContext) return;
  const bounds = microCanvas.getBoundingClientRect();
  if (!bounds.width || !bounds.height) return;
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(Math.round(bounds.width * pixelRatio), 1);
  const height = Math.max(Math.round(bounds.height * pixelRatio), 1);
  if (microCanvas.width !== width || microCanvas.height !== height) {
    microCanvas.width = width;
    microCanvas.height = height;
  }
}

function renderMicro3D(pressure) {
  if (!microCanvas || !microContext || activeMicroView !== "3d") return;
  resizeCanvas();

  const width = microCanvas.width;
  const height = microCanvas.height;
  const context = microContext;
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const scaleX = (width * 0.84) / (FIELD_SIZE * 2);
  const scaleY = (height * 0.5) / (FIELD_SIZE * 2);
  const heightScale = height * 0.24;
  const originX = width * 0.5;
  const originY = height * 0.34;
  const threshold = contactThreshold(pressure);

  const project = (column, row, surfaceHeight) => ({
    x: originX + (column - row) * scaleX,
    y: originY + (column + row) * scaleY - surfaceHeight * heightScale
  });

  context.clearRect(0, 0, width, height);

  const background = context.createRadialGradient(
    width * 0.48,
    height * 0.46,
    0,
    width * 0.5,
    height * 0.46,
    width * 0.72
  );
  background.addColorStop(0, "#1b211d");
  background.addColorStop(1, "#0c0f0d");
  context.fillStyle = background;
  context.fillRect(0, 0, width, height);

  context.lineWidth = Math.max(pixelRatio * 0.55, 0.7);
  for (let row = 0; row < FIELD_SIZE - 1; row += 1) {
    for (let column = 0; column < FIELD_SIZE - 1; column += 1) {
      const heights = [
        surfaceField[row][column],
        surfaceField[row][column + 1],
        surfaceField[row + 1][column + 1],
        surfaceField[row + 1][column]
      ];
      const average = heights.reduce((sum, value) => sum + value, 0) / heights.length;
      const coupled = average >= threshold;
      const points = [
        project(column, row, heights[0]),
        project(column + 1, row, heights[1]),
        project(column + 1, row + 1, heights[2]),
        project(column, row + 1, heights[3])
      ];

      context.beginPath();
      context.moveTo(points[0].x, points[0].y);
      points.slice(1).forEach((point) => context.lineTo(point.x, point.y));
      context.closePath();

      if (coupled) {
        const amber = Math.round(124 + pressure * 58 + average * 44);
        context.fillStyle = `rgb(${amber}, ${Math.round(amber * 0.68)}, ${Math.round(amber * 0.18)})`;
        context.strokeStyle = "rgba(255, 210, 104, 0.24)";
      } else {
        const tone = Math.round(55 + average * 74);
        context.fillStyle = `rgb(${Math.round(tone * 0.75)}, ${tone}, ${Math.round(tone * 0.91)})`;
        context.strokeStyle = "rgba(210, 228, 220, 0.07)";
      }

      context.fill();
      context.stroke();
    }
  }

  const membraneHeight = Math.max(threshold, 0.05);
  context.lineWidth = Math.max(pixelRatio, 1);
  context.strokeStyle = "rgba(4, 6, 5, 0.48)";
  for (let row = 0; row < FIELD_SIZE; row += 4) {
    context.beginPath();
    for (let column = 0; column < FIELD_SIZE; column += 1) {
      const localSurface = surfaceField[row][column];
      const membrane = Math.max(membraneHeight, localSurface + 0.025);
      const point = project(column, row, membrane);
      if (column === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    }
    context.stroke();
  }

  const labelSize = Math.max(Math.round(width * 0.017), 9 * pixelRatio);
  context.font = `${labelSize}px "Cascadia Mono", Consolas, monospace`;
  context.fillStyle = "rgba(222, 229, 222, 0.52)";
  context.textAlign = "left";
  context.fillText("P2500-INSPIRED HEIGHT FIELD", 18 * pixelRatio, 28 * pixelRatio);
  context.fillStyle = "rgba(227, 161, 40, 0.82)";
  context.fillText(
    `${Math.round(contactRatio(pressure) * 100)}% COUPLED / QUALITATIVE`,
    18 * pixelRatio,
    47 * pixelRatio
  );
}

function setActiveMicroView(view, focus = false) {
  activeMicroView = view;
  microTabs.forEach((tab) => {
    const isActive = tab.id === `micro-tab-${view}`;
    tab.setAttribute("aria-selected", String(isActive));
    tab.tabIndex = isActive ? 0 : -1;
    if (isActive && focus) tab.focus();
  });
  microPanels.forEach((panel) => {
    panel.hidden = panel.id !== `micro-panel-${view}`;
  });
  if (view === "3d") {
    requestAnimationFrame(() => renderMicro3D(currentPressure));
  }
}

function render(value) {
  const pressure = Math.min(Math.max(Number(value), 0), 1);
  const percent = Math.round(pressure * 100);
  const state = stateFor(pressure);
  const ratio = contactRatio(pressure);

  currentPressure = pressure;
  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--signal-level", `${percent}%`);
  root.style.setProperty("--coupling-width", `${10 + pressure * 56}%`);
  root.style.setProperty("--reflection-opacity", (0.76 - pressure * 0.62).toFixed(3));
  root.style.setProperty("--camera-darkness", (0.2 + pressure * 0.76).toFixed(3));

  if (pressureInput) pressureInput.value = String(percent);
  if (pressurePercent) pressurePercent.value = `${percent}%`;
  if (toolbarState) toolbarState.value = state.title;
  if (stateIndex) stateIndex.textContent = state.index;
  if (stateCopy) stateCopy.textContent = state.copy;
  if (contactFraction) contactFraction.value = `${Math.round(ratio * 100)}%`;
  if (cameraIntensity) cameraIntensity.value = state.intensity;
  if (microCanvas) {
    microCanvas.setAttribute(
      "aria-label",
      `3D contact field, ${state.title}. Qualitative coupled fraction ${Math.round(ratio * 100)} percent.`
    );
  }

  stateItems.forEach((item) => {
    const isActive = item.dataset.state === state.key;
    item.classList.toggle("is-active", isActive);
    if (isActive) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });

  renderMacro(pressure);
  renderMicro2D(pressure);
  renderMicro3D(pressure);
}

function stopPlayback() {
  isPlaying = false;
  startedAt = 0;
  cancelAnimationFrame(frame);
  playButton?.setAttribute("aria-pressed", "false");
  if (playLabel) playLabel.textContent = "Run once";
}

function tick(now) {
  if (!startedAt) startedAt = now;
  const progress = Math.min((now - startedAt) / 2300, 1);
  const eased = 1 - Math.pow(1 - progress, 3);
  render(eased);

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
  playButton?.setAttribute("aria-pressed", "true");
  if (playLabel) playLabel.textContent = "Pause";
  render(0);
  frame = requestAnimationFrame(tick);
}

function togglePlayback() {
  if (isPlaying) stopPlayback();
  else startPlayback();
}

function animateReveal(element) {
  if (reduceMotion.matches || typeof element.animate !== "function") return;
  element.animate(
    [
      { opacity: 0, transform: "translateY(16px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    {
      duration: 520,
      easing: "cubic-bezier(0.23, 1, 0.32, 1)",
      fill: "both"
    }
  );
}

function revealContent() {
  const items = [...document.querySelectorAll("[data-reveal]")];
  if (reduceMotion.matches || !("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateReveal(entry.target);
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -6% 0px" }
  );

  items.forEach((item) => observer.observe(item));
}

microTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const view = tab.id.endsWith("3d") ? "3d" : "2d";
    setActiveMicroView(view);
  });

  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let target = event.key === "ArrowLeft" ? "2d" : "3d";
    if (event.key === "Home") target = "2d";
    if (event.key === "End") target = "3d";
    setActiveMicroView(target, true);
  });
});

playButton?.addEventListener("click", togglePlayback);

pressureInput?.addEventListener("input", (event) => {
  stopPlayback();
  render(Number(event.currentTarget.value) / 100);
});

pressureInput?.addEventListener("pointerdown", stopPlayback);
pressureInput?.addEventListener("keydown", stopPlayback);

window.addEventListener("resize", () => {
  if (activeMicroView === "3d") renderMicro3D(currentPressure);
});

render(currentPressure);
setActiveMicroView("2d");
if (microContext) canvasFallback?.setAttribute("hidden", "");
revealContent();
