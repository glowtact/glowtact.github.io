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
const cameraContact = document.querySelector(".camera-contact");

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
const macroIndenter = document.querySelector("#macro-indenter");

const microSurfaceFill = document.querySelector("#micro-surface-fill");
const microSvg = document.querySelector("#micro-svg");
const microSurfaceLine = document.querySelector("#micro-surface-line");
const microMembrane = document.querySelector("#micro-membrane");
const microMembraneShadow = document.querySelector("#micro-membrane-shadow");
const microGapArea = document.querySelector("#micro-gap-area");
const microContactPoints = document.querySelector("#micro-contact-points");

const FIELD_SIZE = 41;
const PROFILE_SIZE = 65;
const FIELD_SEED = 2500;
const MICRO_CLEARANCE = 2.5;
const MACRO_INITIAL_GAP = 18;
const MACRO_MIN_GAP = 1.8;
const INDENTER_CONTACT_PRESSURE = 0.22;
const SVG_NS = "http://www.w3.org/2000/svg";

let activeMicroView = "2d";
let currentPressure = Number(pressureInput?.value ?? 0) / 100;
let isPlaying = false;
let startedAt = 0;
let frame = 0;
let stepTimer = 0;

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

/**
 * One continuous roughness surface for the whole microscope patch.
 *
 * The 3D field and the 2D section are both sampled from this single model, so
 * the two views describe the same physical texture and share one height scale.
 * That is what lets a single membrane plane mean the same thing in every view.
 */
function createRoughness(seed) {
  const random = seededRandom(seed);
  const gridSize = 8;
  const asperities = [];

  for (let row = 0; row < gridSize; row += 1) {
    for (let column = 0; column < gridSize; column += 1) {
      const radiusMajor = 0.024 + random() * 0.04;
      const radiusMinor = 0.016 + random() * 0.03;
      const angle = random() * Math.PI;
      const shoulderAngle = random() * Math.PI * 2;
      const shoulderDistance = radiusMajor * (0.35 + random() * 0.65);
      asperities.push({
        x: (column + 0.06 + random() * 0.88) / gridSize,
        y: (row + 0.06 + random() * 0.88) / gridSize,
        radiusMajor,
        radiusMinor,
        angle,
        cuspPower: 0.72 + random() * 0.66,
        height: 0.5 + random() * 0.62,
        shoulderX: Math.cos(shoulderAngle) * shoulderDistance,
        shoulderY: Math.sin(shoulderAngle) * shoulderDistance,
        shoulderScale: 0.72 + random() * 0.68,
        shoulderHeight: random() < 0.72 ? 0.1 + random() * 0.2 : 0
      });
    }
  }

  return function sampleRoughness(x, y) {
    const base =
      0.075 +
      Math.sin(x * Math.PI * 3.1 + 0.7) * 0.025 +
      Math.cos(y * Math.PI * 2.6 + 1.2) * 0.022 +
      Math.sin((x - y) * Math.PI * 2.2) * 0.014;
    let asperityHeight = 0;

    asperities.forEach((asperity) => {
      const cosine = Math.cos(asperity.angle);
      const sine = Math.sin(asperity.angle);
      const dx = x - asperity.x;
      const dy = y - asperity.y;
      const rotatedX = dx * cosine + dy * sine;
      const rotatedY = -dx * sine + dy * cosine;
      const distance = Math.sqrt(
        Math.pow(rotatedX / asperity.radiusMajor, 2) +
          Math.pow(rotatedY / asperity.radiusMinor, 2)
      );
      const mainHeight =
        asperity.height *
        Math.exp(-Math.pow(distance, asperity.cuspPower) * 2.7);
      const shoulderDx = dx - asperity.shoulderX;
      const shoulderDy = dy - asperity.shoulderY;
      const shoulderX = shoulderDx * cosine + shoulderDy * sine;
      const shoulderY = -shoulderDx * sine + shoulderDy * cosine;
      const shoulderDistance = Math.sqrt(
        Math.pow(
          shoulderX / (asperity.radiusMajor * asperity.shoulderScale),
          2
        ) +
          Math.pow(
            shoulderY / (asperity.radiusMinor * asperity.shoulderScale),
            2
          )
      );
      const shoulderHeight =
        asperity.height *
        asperity.shoulderHeight *
        Math.exp(-Math.pow(shoulderDistance, 1.1) * 2.25);
      asperityHeight = Math.max(asperityHeight, mainHeight + shoulderHeight);
    });

    return Math.max(0, base) + asperityHeight;
  };
}

const sampleRoughness = createRoughness(FIELD_SEED);

function sampleFieldGrid(size) {
  const values = [];
  for (let row = 0; row < size; row += 1) {
    const line = [];
    for (let column = 0; column < size; column += 1) {
      line.push(
        sampleRoughness(column / (size - 1), row / (size - 1))
      );
    }
    values.push(line);
  }
  return values;
}

const rawField = sampleFieldGrid(FIELD_SIZE);
const rawHeights = rawField.flat();
const heightMinimum = Math.min(...rawHeights);
const heightRange = Math.max(
  Math.max(...rawHeights) - heightMinimum,
  Number.EPSILON
);

/** Shared height scale so every view reads the same roughness amplitude. */
function normalizeHeight(height) {
  return Math.min(Math.max((height - heightMinimum) / heightRange, 0), 1);
}

const surfaceField = rawField.map((line) => line.map(normalizeHeight));

function sampleSection(size, y) {
  return Array.from({ length: size }, (_, index) =>
    normalizeHeight(sampleRoughness(index / (size - 1), y))
  );
}

function fractionAbove(heights, plane) {
  let count = 0;
  for (let index = 0; index < heights.length; index += 1) {
    if (heights[index] >= plane) count += 1;
  }
  return count / heights.length;
}

/** Probe planes used to compare a candidate slice against the whole field. */
const DISTRIBUTION_PROBES = Array.from(
  { length: 19 },
  (_, index) => (index + 1) / 20
);
const fieldHeights = surfaceField.flat();
const fieldProfileCurve = DISTRIBUTION_PROBES.map((plane) =>
  fractionAbove(fieldHeights, plane)
);

/**
 * The section is a genuine slice through the field rather than a separate
 * synthetic profile. The slice row is chosen deterministically as the line
 * whose height distribution best matches the whole field, so the section and
 * the 3D view report the same coupled fraction for the same membrane plane.
 * A legibility floor keeps the slice from landing in a featureless valley.
 */
function chooseSectionRow(size, candidates = 360) {
  let bestY = 0.5;
  let bestScore = Infinity;

  for (let index = 0; index < candidates; index += 1) {
    const y = (index + 0.5) / candidates;
    const heights = sampleSection(size, y);
    const peaks = heights.filter((height) => height >= 0.42).length;
    // Require enough asperity material for the section to read as texture.
    if (peaks < 3) continue;

    let score = 0;
    for (let probe = 0; probe < DISTRIBUTION_PROBES.length; probe += 1) {
      const difference =
        fractionAbove(heights, DISTRIBUTION_PROBES[probe]) -
        fieldProfileCurve[probe];
      score += difference * difference;
    }
    if (score < bestScore) {
      bestScore = score;
      bestY = y;
    }
  }
  return bestY;
}

const SECTION_ROW = chooseSectionRow(PROFILE_SIZE);

/** True heights of the section in the shared roughness scale. */
const sectionHeights = sampleSection(PROFILE_SIZE, SECTION_ROW);
const sectionLow = Math.min(...sectionHeights);
const sectionHigh = Math.max(...sectionHeights);
const sectionSpan = Math.max(sectionHigh - sectionLow, Number.EPSILON);

/**
 * Vertical exaggeration for the drawn section, the same convention the device
 * view uses for the ~9 um texture.
 *
 * Any strictly increasing map is safe here: the membrane plane is pushed
 * through the identical transform, so the set of points above it -- and hence
 * the coupled fraction the section reports -- is bit-for-bit what it would be
 * at true scale. Only the drawn amplitude changes.
 *
 * A plain min/max stretch is not enough on its own. This surface is strongly
 * skewed (its median sits near a tenth of its peak), so linear rescaling still
 * renders as a flat line punctuated by a couple of spikes. The gamma lifts the
 * low and mid range into the panel so the texture reads as texture.
 */
const SECTION_DISPLAY_GAMMA = 0.45;

function sectionDisplayHeight(height) {
  const normalized = (height - sectionLow) / sectionSpan;
  if (normalized <= 0) return 0;
  return Math.pow(normalized, SECTION_DISPLAY_GAMMA);
}

const surfaceProfile = sectionHeights.map(sectionDisplayHeight);

/**
 * Qualitative real-contact-area law.
 *
 * Contact starts on the single highest asperity, accelerates as the bulk of
 * the height distribution is swallowed, then saturates: the membrane cannot
 * reach the deepest valleys, so a residual air fraction always survives. The
 * curve is a logistic in load, which reproduces that slow-fast-slow shape.
 */
const CONTACT_SATURATION = 0.92;
const CONTACT_ONSET = 2.2;
const CONTACT_BIAS = 1.9;

function targetContactFraction(pressure) {
  const load = Math.min(Math.max(pressure, 0), 1);
  if (load <= 0) return 0;
  if (load >= 1) return CONTACT_SATURATION;
  const rise = Math.pow(load, CONTACT_ONSET);
  const fall = Math.pow(1 - load, CONTACT_ONSET);
  return (CONTACT_SATURATION * rise) / (rise + CONTACT_BIAS * fall);
}

/**
 * Height of the descending membrane plane that leaves the requested fraction
 * of a sampled surface above it.
 */
function planeHeightFor(sortedDescending, fraction) {
  if (!sortedDescending.length) return 1;
  if (fraction <= 0) return sortedDescending[0] + 1e-6;
  const count = Math.max(
    1,
    Math.min(sortedDescending.length, Math.round(fraction * sortedDescending.length))
  );
  return sortedDescending[count - 1];
}

/** Coupled-area breakpoints that separate the three narrated states. */
const LOCAL_COUPLING_AREA = 0.012;
const EXPANDED_COUPLING_AREA = 0.4;

/**
 * The narrated state is read from the coupled area rather than from the slider
 * position, so the caption always describes what the views actually show.
 */
function stateFor(pressure, coupledArea = contactRatio(couplingPressureFor(pressure))) {
  if (pressure < INDENTER_CONTACT_PRESSURE || coupledArea < LOCAL_COUPLING_AREA) {
    return {
      key: "gap",
      index: "STATE 00",
      title: "Air gap",
      reflection: "Diffuse reflection",
      intensity: "No signal",
      copy:
        "The indenter is approaching the membrane. A thin microscopic air gap still separates the membrane from the gel, so the camera sees no dark contact signal."
    };
  }

  if (coupledArea < EXPANDED_COUPLING_AREA) {
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
      "Contact islands merge until only the deepest valleys still trap air. The absorbing region stops spreading and keeps darkening as contact grows more intimate."
  };
}

/** Sub-samples per cell axis when measuring the coupled area of a cell. */
const CELL_SUBSAMPLES = 4;

/**
 * Penetration below the plane at which a patch reaches full optical contact.
 *
 * Measured across 0.055-0.22 this term behaves as a near-pure gain: the shape
 * of the coupling curve is unchanged (half-load reaches 29% of the full-load
 * value at every value tested), because the penetration distribution rescales
 * self-similarly as the plane descends. Its real job is therefore to hold
 * first-touch and marginal patches optically weak, not to bend the curve. The
 * value is set at the low end so that patches pressed fully home do reach
 * complete coupling, which is what lets the camera approach saturation.
 */
const INTIMACY_DEPTH = 0.055;

/** Optical coupling of a patch that touches but is not yet pressed home. */
const CONTACT_FLOOR = 0.55;

/** Display gamma applied to the physical coupling before it is drawn. */
const CAMERA_GAMMA = 0.6;

/**
 * Fraction of the patch that lies above a plane, measured on the interpolated
 * surface rather than by counting grid corners. This is the quantity the 3D
 * view actually shades, so solving the plane against it keeps the contact law
 * and the rendered image describing the same number.
 */
function measureCoupledArea(plane) {
  const cellSpan = FIELD_SIZE - 1;
  const subSampleCount = CELL_SUBSAMPLES * CELL_SUBSAMPLES;
  let covered = 0;

  for (let row = 0; row < cellSpan; row += 1) {
    for (let column = 0; column < cellSpan; column += 1) {
      const topLeft = surfaceField[row][column];
      const topRight = surfaceField[row][column + 1];
      const bottomRight = surfaceField[row + 1][column + 1];
      const bottomLeft = surfaceField[row + 1][column];
      if (
        topLeft < plane &&
        topRight < plane &&
        bottomRight < plane &&
        bottomLeft < plane
      ) {
        continue;
      }
      for (let sy = 0; sy < CELL_SUBSAMPLES; sy += 1) {
        const v = (sy + 0.5) / CELL_SUBSAMPLES;
        for (let sx = 0; sx < CELL_SUBSAMPLES; sx += 1) {
          const u = (sx + 0.5) / CELL_SUBSAMPLES;
          const height =
            topLeft * (1 - u) * (1 - v) +
            topRight * u * (1 - v) +
            bottomLeft * (1 - u) * v +
            bottomRight * u * v;
          if (height >= plane) covered += 1;
        }
      }
    }
  }

  return covered / (cellSpan * cellSpan * subSampleCount);
}

/** Plane heights sampled once so the inverse lookup stays cheap per frame. */
const PLANE_TABLE_SIZE = 161;
const planeAreaTable = Array.from({ length: PLANE_TABLE_SIZE }, (_, index) => {
  const plane = 1 - index / (PLANE_TABLE_SIZE - 1);
  return { plane, area: measureCoupledArea(plane) };
});

/** Invert the measured area curve to find the plane that delivers an area. */
function planeForArea(targetArea) {
  if (targetArea <= 0) return 1 + 1e-6;
  for (let index = 1; index < planeAreaTable.length; index += 1) {
    const upper = planeAreaTable[index - 1];
    const lower = planeAreaTable[index];
    if (lower.area >= targetArea) {
      const span = lower.area - upper.area;
      const blend = span > 1e-9 ? (targetArea - upper.area) / span : 0;
      return upper.plane + (lower.plane - upper.plane) * blend;
    }
  }
  return planeAreaTable[planeAreaTable.length - 1].plane;
}

/**
 * The membrane plane is a single height in the shared roughness scale. Every
 * view resolves contact against this one number, so the section, the field and
 * the camera cannot drift apart.
 */
function membranePlaneFor(pressure) {
  return planeForArea(targetContactFraction(pressure));
}

function contactThreshold(pressure) {
  return membranePlaneFor(pressure);
}

/**
 * The same membrane plane, expressed in the section's exaggerated display
 * scale. Because the exaggeration is affine and increasing, the set of points
 * above this plane is identical to the set above the shared plane, so the
 * section reports the same coupled fraction it would at true scale.
 */
function profileThreshold(pressure) {
  return sectionDisplayHeight(membranePlaneFor(pressure));
}

/** Single definition of coupled area, so every caller reports one number. */
function contactRatio(pressure) {
  return microContactModel(pressure).area;
}

/**
 * Resolve the coupled area and coupling intimacy of the patch for one membrane
 * plane.
 *
 * `area` is the true fraction of the patch below the plane, measured by
 * bilinear sub-sampling rather than a corner vote, so it agrees with the plane
 * quantile and with the 2D section. `coupling` weights that area by how deeply
 * each contact is pressed, which is what the camera actually darkens with:
 * once the area saturates, contacts keep getting more intimate.
 */
function microContactModel(couplingPressure) {
  const fieldThreshold = contactThreshold(couplingPressure);
  const sectionThreshold = profileThreshold(couplingPressure);
  const cellStrengths = [];
  const cellCoverages = [];
  const maskBits = [];
  const quadrants = [0, 0, 0, 0];
  const cellSpan = FIELD_SIZE - 1;
  const subSampleCount = CELL_SUBSAMPLES * CELL_SUBSAMPLES;
  let contactCells = 0;
  let coveredArea = 0;
  let couplingSum = 0;
  let penetrationSum = 0;
  let totalStrength = 0;
  let weightedX = 0;
  let weightedY = 0;
  let weightedX2 = 0;
  let weightedY2 = 0;

  for (let row = 0; row < cellSpan; row += 1) {
    const strengthRow = [];
    const coverageRow = [];
    for (let column = 0; column < cellSpan; column += 1) {
      const topLeft = surfaceField[row][column];
      const topRight = surfaceField[row][column + 1];
      const bottomRight = surfaceField[row + 1][column + 1];
      const bottomLeft = surfaceField[row + 1][column];

      let covered = 0;
      let penetration = 0;
      for (let sy = 0; sy < CELL_SUBSAMPLES; sy += 1) {
        const v = (sy + 0.5) / CELL_SUBSAMPLES;
        for (let sx = 0; sx < CELL_SUBSAMPLES; sx += 1) {
          const u = (sx + 0.5) / CELL_SUBSAMPLES;
          const height =
            topLeft * (1 - u) * (1 - v) +
            topRight * u * (1 - v) +
            bottomLeft * (1 - u) * v +
            bottomRight * u * v;
          const depth = height - fieldThreshold;
          if (depth >= 0) {
            covered += 1;
            penetration += depth;
          }
        }
      }

      const coverage = covered / subSampleCount;
      // Mean penetration across the coupled part of the cell.
      const meanPenetration = covered ? penetration / covered : 0;
      const intimacy = Math.min(meanPenetration / INTIMACY_DEPTH, 1);
      // Optical coupling density: how much of the cell touches, and how hard.
      const contactStrength =
        coverage * (CONTACT_FLOOR + (1 - CONTACT_FLOOR) * intimacy);

      strengthRow.push(contactStrength);
      coverageRow.push(coverage);
      maskBits.push(coverage > 0 ? 1 : 0);
      coveredArea += coverage;
      couplingSum += contactStrength;

      if (coverage > 0) {
        contactCells += 1;
        penetrationSum += meanPenetration * coverage;
        const x = (column + 0.5) / cellSpan;
        const y = (row + 0.5) / cellSpan;
        const quadrant =
          (row >= cellSpan / 2 ? 2 : 0) + (column >= cellSpan / 2 ? 1 : 0);
        quadrants[quadrant] += 1;
        totalStrength += contactStrength;
        weightedX += x * contactStrength;
        weightedY += y * contactStrength;
        weightedX2 += x * x * contactStrength;
        weightedY2 += y * y * contactStrength;
      }
    }
    cellStrengths.push(strengthRow);
    cellCoverages.push(coverageRow);
  }

  const cellCount = cellSpan * cellSpan;
  const centerX = totalStrength ? weightedX / totalStrength : 0.5;
  const centerY = totalStrength ? weightedY / totalStrength : 0.5;
  const spreadX = totalStrength
    ? Math.sqrt(Math.max(weightedX2 / totalStrength - centerX * centerX, 0))
    : 0;
  const spreadY = totalStrength
    ? Math.sqrt(Math.max(weightedY2 / totalStrength - centerY * centerY, 0))
    : 0;
  const area = coveredArea / cellCount;
  const coupling = couplingSum / cellCount;
  // Window-level gap closure: penetration integrated over the whole window,
  // not averaged over the coupled part. Averaging is not monotone, because
  // freshly recruited marginal contact enters at zero depth and dilutes the
  // mean even while every existing patch is pressed harder. The integral is
  // monotone in the plane by construction, so it can be reported as a state.
  const intimacy = Math.min(penetrationSum / cellCount / INTIMACY_DEPTH, 1);

  return {
    fieldThreshold,
    sectionThreshold,
    area,
    coupling,
    intimacy,
    contactCells,
    flattenedCells: contactCells,
    quadrants,
    centerX,
    centerY,
    spreadX,
    spreadY,
    cellStrengths,
    cellCoverages,
    maskSignature: numericSignature(maskBits)
  };
}

function couplingPressureFor(pressure) {
  const normalized = Math.min(
    Math.max((pressure - INDENTER_CONTACT_PRESSURE) / (1 - INDENTER_CONTACT_PRESSURE), 0),
    1
  );
  return Math.pow(normalized, 0.75);
}

function indenterYFor(pressure) {
  const approach = Math.min(pressure / INDENTER_CONTACT_PRESSURE, 1);
  const coupling = couplingPressureFor(pressure);
  return 34 + approach * 29 + coupling * 24;
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

function angularPath(points) {
  if (!points.length) return "";
  return points
    .map(
      (point, index) =>
        `${index === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`
    )
    .join(" ");
}

function numericSignature(values) {
  let hash = 2166136261;
  values.forEach((value) => {
    hash ^= Math.round(value * 1000000);
    hash = Math.imul(hash, 16777619);
  });
  return (hash >>> 0).toString(16).padStart(8, "0");
}

const profileSignature = numericSignature(surfaceProfile);
const fieldSignature = numericSignature(surfaceField.flat());

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

function renderMacro(pressure, contactModel = microContactModel(couplingPressureFor(pressure))) {
  if (!macroMembrane || !macroGel) return;

  const couplingPressure = couplingPressureFor(pressure);
  const surfacePoints = [];
  const membranePoints = [];
  const start = 70;
  const end = 850;
  const samples = 65;
  const centerIndex = Math.floor(samples / 2);

  for (let index = 0; index < samples; index += 1) {
    const x = start + (index / (samples - 1)) * (end - start);
    const indentation = macroIndentationWeight(x);
    const surfaceY = macroSurfaceY(x);
    const localGap =
      MACRO_INITIAL_GAP -
      indentation * couplingPressure * (MACRO_INITIAL_GAP - MACRO_MIN_GAP);
    const membraneY = surfaceY - Math.max(MACRO_MIN_GAP, localGap);

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
  if (macroAirGap) {
    const centerGap = surfacePoints[centerIndex].y - membranePoints[centerIndex].y;
    macroAirGap.dataset.centerClearance = centerGap.toFixed(3);
  }
  if (macroIndenter) {
    const indenterY = indenterYFor(pressure);
    macroIndenter.dataset.contactState =
      pressure >= INDENTER_CONTACT_PRESSURE ? "touching" : "approaching";
    macroIndenter.dataset.distanceToMembrane =
      Math.max(0, INDENTER_CONTACT_PRESSURE - pressure).toFixed(3);
    root.style.setProperty("--indenter-y", `${indenterY.toFixed(2)}px`);
  }

  const ratio = contactModel.area;
  const centerX = start + contactModel.centerX * (end - start);
  const contactChordWidth =
    ratio > 0 ? Math.min(92, Math.max(10, 14 + Math.sqrt(ratio) * 104)) : 0;
  const halfChord = contactChordWidth / 2;
  const contactChord =
    contactChordWidth > 0
      ? surfacePoints.filter(
          (point) => Math.abs(point.x - centerX) <= halfChord
        )
      : [];
  if (contactChord.length === 1) {
    const point = contactChord[0];
    contactChord.unshift({
      x: point.x - halfChord,
      y: macroSurfaceY(point.x - halfChord)
    });
    contactChord.push({
      x: point.x + halfChord,
      y: macroSurfaceY(point.x + halfChord)
    });
  }
  macroCouplingLine?.setAttribute(
    "d",
    contactChord.length > 1 ? smoothPath(contactChord) : ""
  );
  if (macroCouplingLine) {
    const deformationSpan = surfacePoints
      .filter((point, index) => {
        const gap = point.y - membranePoints[index].y;
        return MACRO_INITIAL_GAP - gap > 1.4;
      })
      .reduce(
        (span, point) => ({
          minimum: Math.min(span.minimum, point.x),
          maximum: Math.max(span.maximum, point.x)
        }),
        { minimum: Infinity, maximum: -Infinity }
      );
    const membraneDeformationSpan =
      deformationSpan.minimum === Infinity
        ? 0
        : deformationSpan.maximum - deformationSpan.minimum;
    macroCouplingLine.dataset.contactMaskSignature = contactModel.maskSignature;
    macroCouplingLine.dataset.contactArea = ratio.toFixed(6);
    macroCouplingLine.dataset.couplingChordWidth = contactChordWidth.toFixed(2);
    macroCouplingLine.dataset.membraneDeformationSpan =
      membraneDeformationSpan.toFixed(2);
  }

  macroCouplingGlow?.setAttribute("rx", String(8 + contactChordWidth * 0.46));
  macroCouplingGlow?.setAttribute("ry", String(10 + Math.sqrt(ratio) * 18));
  macroFieldOfView?.setAttribute("opacity", (0.18 + ratio * 0.72).toFixed(3));
  macroCameraAperture?.setAttribute("opacity", (0.48 + ratio * 0.52).toFixed(3));
}

function renderMicro2D(pressure, contactModel = microContactModel(couplingPressureFor(pressure))) {
  if (!microSurfaceFill || !microMembrane) return;

  const couplingPressure = couplingPressureFor(pressure);
  const threshold = contactModel.sectionThreshold;
  const contactIndentations = surfaceProfile.map((height) =>
    Math.max(height - threshold, 0)
  );
  const preliminaryProfile = surfaceProfile.map((height, index) => {
    const localIndentation = contactIndentations[index];
    const tipFlattening =
      localIndentation > 0
        ? Math.min(localIndentation * 0.62 + couplingPressure * 0.055, 0.16)
        : 0;
    const lateralWidening = contactIndentations.reduce((widening, indentation, neighborIndex) => {
      if (indentation <= 0 || neighborIndex === index) return widening;
      const distance = Math.abs(neighborIndex - index);
      const radius = 1.4 + Math.sqrt(indentation) * 6;
      return Math.max(
        widening,
        indentation * 0.2 * Math.exp(-(distance * distance) / (radius * radius))
      );
    }, 0);
    return Math.min(Math.max(height - tipFlattening + lateralWidening, 0), 1);
  });
  const deformedProfile = [...preliminaryProfile];
  let capRun = [];
  const applyCurvedCap = () => {
    if (!capRun.length) return;
    const left = capRun[0];
    const right = capRun[capRun.length - 1];
    const center = (left + right) / 2;
    const halfWidth = Math.max((right - left) / 2, 1);
    const maxIndentation = capRun.reduce(
      (maximum, index) => Math.max(maximum, contactIndentations[index]),
      0
    );
    const capBase =
      threshold + Math.min(maxIndentation * 0.18 + couplingPressure * 0.024, 0.055);
    const capCurvature = Math.min(
      maxIndentation * 0.075 + couplingPressure * 0.018,
      0.04
    );
    capRun.forEach((index) => {
      const normalizedDistance = (index - center) / halfWidth;
      const curvedLift = capCurvature * (1 - normalizedDistance * normalizedDistance);
      const target = capBase + curvedLift;
      deformedProfile[index] =
        target + (preliminaryProfile[index] - target) * 0.08;
    });
    capRun = [];
  };
  contactIndentations.forEach((indentation, index) => {
    if (indentation > 0) capRun.push(index);
    else applyCurvedCap();
  });
  applyCurvedCap();
  const surfacePoints = deformedProfile.map((height, index) => {
    return {
      x: 28 + (index / (surfaceProfile.length - 1)) * 464,
      y: 236 - height * 88
    };
  });
  const desiredY = 236 - threshold * 88;
  const constraintThreshold = threshold - MICRO_CLEARANCE / 88;
  const contactConstraints = surfacePoints.filter(
    (_, index) => surfaceProfile[index] >= constraintThreshold
  );
  const compliancePenalty = 0.004 + pressure * 0.016;
  const envelope = surfacePoints.map((point, index) => {
    const xNormal = index / (surfacePoints.length - 1);
    const planeY = desiredY + (xNormal - 0.5) * 2.5;
    return contactConstraints.reduce((membraneY, constraint) => {
      const distance = point.x - constraint.x;
      const constraintY =
        constraint.y - MICRO_CLEARANCE + distance * distance * compliancePenalty;
      return Math.min(membraneY, constraintY);
    }, planeY);
  });
  const clearanceLimits = surfacePoints.map(
    (point) => point.y - MICRO_CLEARANCE
  );
  const projectClearance = (values) =>
    values.map((height, index) => Math.min(height, clearanceLimits[index]));
  let compliantEnvelope = projectClearance(envelope);
  for (let pass = 0; pass < 2; pass += 1) {
    const smoothedEnvelope = compliantEnvelope.map(
      (height, index, values) => {
        if (index === 0 || index === values.length - 1) return height;
        const smoothed =
          values[index - 1] * 0.24 + height * 0.52 + values[index + 1] * 0.24;
        return Math.min(smoothed, envelope[index]);
      }
    );
    compliantEnvelope = projectClearance(smoothedEnvelope);
  }
  compliantEnvelope = projectClearance(compliantEnvelope);
  const membranePoints = surfacePoints.map((point, index) => ({
    x: point.x,
    y: compliantEnvelope[index]
  }));
  const contactSampleIndices = contactIndentations
    .map((indentation, index) => (indentation > 0 ? index : -1))
    .filter((index) => index >= 0);
  const contactThirdCounts = [0, 0, 0];
  contactSampleIndices.forEach((index) => {
    contactThirdCounts[Math.min(Math.floor((index * 3) / PROFILE_SIZE), 2)] += 1;
  });
  const minimumClearance = Math.min(
    ...surfacePoints.map(
      (point, index) => point.y - membranePoints[index].y
    )
  );

  if (microSvg) {
    microSvg.dataset.minimumClearance = minimumClearance.toFixed(6);
    microSvg.dataset.contactSamples = String(contactSampleIndices.length);
    microSvg.dataset.contactThirds = contactThirdCounts.join(",");
    microSvg.dataset.profileSignature = profileSignature;
    microSvg.dataset.contactMaskSignature = contactModel.maskSignature;
    microSvg.dataset.contactArea = contactModel.area.toFixed(6);
    microSvg.dataset.contactCentroid = `${contactModel.centerX.toFixed(4)},${contactModel.centerY.toFixed(4)}`;
    microSvg.dataset.contactSpread = `${contactModel.spreadX.toFixed(4)},${contactModel.spreadY.toFixed(4)}`;
  }

  const surfacePath = angularPath(surfacePoints);
  const membranePath = smoothPath(membranePoints);
  microSurfaceFill.setAttribute("d", `${surfacePath} L492 300 L28 300 Z`);
  microSurfaceLine?.setAttribute("d", surfacePath);
  microMembrane.setAttribute("d", membranePath);
  microMembraneShadow?.setAttribute("d", membranePath);
  microGapArea?.setAttribute("d", areaBetween(membranePoints, surfacePoints));

  if (!microContactPoints) return;
  microContactPoints.replaceChildren();
  let run = [];
  const plateauWidths = [];
  const contactCapWidths = [];
  const contactFootprintWidths = [];
  const appendContactRun = () => {
    if (!run.length) return;
    const peakPoints = run.filter((point) => {
      const previous = surfaceProfile[Math.max(point.index - 1, 0)];
      const next = surfaceProfile[Math.min(point.index + 1, surfaceProfile.length - 1)];
      return surfaceProfile[point.index] >= previous && surfaceProfile[point.index] >= next;
    });
    const peaks = peakPoints.length
      ? peakPoints
      : [
          run.reduce((highest, point) =>
            surfaceProfile[point.index] > surfaceProfile[highest.index]
              ? point
              : highest
          )
        ];

    peaks.forEach((peak) => {
      const localIndentation = contactIndentations[peak.index];
      const capWidth = Math.min(
        24,
        Math.max(7.5, 5.5 + Math.sqrt(Math.max(localIndentation, 0)) * 18)
      );
      const footprintWidth = Math.max(
        capWidth / 0.54,
        22 + Math.sqrt(Math.max(localIndentation, 0)) * 46
      );
      const capCurvature = Math.min(1.1 + localIndentation * 6.2, 3.4);
      const centerX = peak.x;
      const leftX = centerX - capWidth / 2;
      const rightX = centerX + capWidth / 2;
      const edgeY = peak.y + capCurvature * 0.35 - 1.1;
      const centerY = peak.y - capCurvature * 0.48 - 1.1;
      plateauWidths.push(capWidth);
      contactCapWidths.push(capWidth);
      contactFootprintWidths.push(footprintWidth);
      const contact = document.createElementNS(SVG_NS, "path");
      contact.setAttribute("class", "micro-contact-segment");
      contact.dataset.capCurvature = capCurvature.toFixed(3);
      contact.dataset.capWidth = capWidth.toFixed(2);
      contact.dataset.footprintWidth = footprintWidth.toFixed(2);
      contact.setAttribute(
        "d",
        `M${leftX.toFixed(2)} ${edgeY.toFixed(2)} Q${centerX.toFixed(2)} ${centerY.toFixed(2)} ${rightX.toFixed(2)} ${edgeY.toFixed(2)}`
      );
      microContactPoints.append(contact);
    });
    run = [];
  };

  surfacePoints.forEach((point, index) => {
    if (contactIndentations[index] > 0) run.push({ ...point, index });
    else appendContactRun();
  });
  appendContactRun();
  if (microSvg) {
    microSvg.dataset.plateauWidths = plateauWidths
      .map((width) => width.toFixed(2))
      .join(",");
    microSvg.dataset.contactCapWidths = contactCapWidths
      .map((width) => width.toFixed(2))
      .join(",");
    microSvg.dataset.contactFootprintWidths = contactFootprintWidths
      .map((width) => width.toFixed(2))
      .join(",");
  }
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

function renderMicro3D(pressure, contactModel = microContactModel(couplingPressureFor(pressure))) {
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
  const couplingPressure = couplingPressureFor(pressure);
  const threshold = contactModel.fieldThreshold;
  let contactCellCount = 0;
  const capCurvature = Math.min(0.012 + couplingPressure * 0.032, 0.04);

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
      const contactStrength = contactModel.cellStrengths[row][column];
      const contactCoverage = contactModel.cellCoverages[row][column];
      const average = heights.reduce((sum, value) => sum + value, 0) / heights.length;
      const flattenedHeights = heights.map((surfaceHeight) => {
        if (contactStrength <= 0) {
          return surfaceHeight;
        }
        const plateauHeight = Math.max(
          threshold - 0.018,
          average - Math.min(couplingPressure * 0.085, 0.085)
        );
        const residualRelief = 0.035 + (1 - contactStrength) * 0.13;
        const curvedTip = capCurvature * Math.min(contactStrength, 1);
        return (
          plateauHeight +
          curvedTip +
          (surfaceHeight - plateauHeight) * residualRelief
        );
      });
      if (contactStrength > 0) {
        contactCellCount += 1;
      }
      const points = [
        project(column, row, flattenedHeights[0]),
        project(column + 1, row, flattenedHeights[1]),
        project(column + 1, row + 1, flattenedHeights[2]),
        project(column, row + 1, flattenedHeights[3])
      ];

      context.beginPath();
      context.moveTo(points[0].x, points[0].y);
      points.slice(1).forEach((point) => context.lineTo(point.x, point.y));
      context.closePath();

      const tone = Math.round(55 + average * 74);
      const baseColor = [Math.round(tone * 0.75), tone, Math.round(tone * 0.91)];
      // Amber extent tracks the cell's coupled fraction directly. An earlier
      // version added a 0.24 floor to any cell with a single coupled
      // sub-sample, which made a 5%-coupled window read as roughly 20% amber
      // and put this view visibly out of step with the section and the
      // readout. Blending proportionally keeps the three views agreeing.
      const contactMix = contactCoverage;
      const color = baseColor.map((channel, index) =>
        Math.round(channel + ([227, 161, 40][index] - channel) * contactMix)
      );
      context.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
      context.strokeStyle = contactStrength
        ? `rgba(255, 218, 126, ${0.12 + contactStrength * 0.34})`
        : "rgba(210, 228, 220, 0.07)";

      context.fill();
      context.stroke();
    }
  }

  microCanvas.dataset.contactCells = String(contactCellCount);
  microCanvas.dataset.contactQuadrants = contactModel.quadrants.join(",");
  microCanvas.dataset.flattenedCells = String(contactModel.flattenedCells);
  microCanvas.dataset.contactMaskSignature = contactModel.maskSignature;
  microCanvas.dataset.contactArea = contactModel.area.toFixed(6);
  microCanvas.dataset.contactCentroid = `${contactModel.centerX.toFixed(4)},${contactModel.centerY.toFixed(4)}`;
  microCanvas.dataset.contactSpread = `${contactModel.spreadX.toFixed(4)},${contactModel.spreadY.toFixed(4)}`;
  microCanvas.dataset.capCurvature = capCurvature.toFixed(4);
  microCanvas.dataset.fieldSignature = fieldSignature;

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
    `${Math.round(contactRatio(couplingPressure) * 100)}% COUPLED / QUALITATIVE`,
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
  const couplingPressure = couplingPressureFor(pressure);
  const contactModel = microContactModel(couplingPressure);
  const ratio = contactModel.area;
  const state = stateFor(pressure, ratio);
  // The membrane absorbs in proportion to how much of the patch is optically
  // coupled and how intimately, so the camera tracks the same quantity the
  // microscope views render instead of saturating on its own schedule.
  const cameraSignal = Math.min(Math.max(contactModel.coupling, 0), 1);
  // Displayed contrast is the physical signal under a display gamma, so faint
  // early coupling stays visible without the response pinning at mid travel.
  const cameraResponse = Math.pow(cameraSignal, CAMERA_GAMMA);
  const cameraDiameter =
    ratio > 0 ? 36 + Math.sqrt(ratio) * 144 + cameraResponse * 22 : 38;
  const annulusStrength = 0.12 + cameraResponse * 0.42;
  const blobX = 50;
  const blobY = 50;

  currentPressure = pressure;
  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--signal-level", `${percent}%`);
  root.style.setProperty("--coupling-width", `${48 + cameraResponse * 162}px`);
  root.style.setProperty("--camera-contact-width", `${cameraDiameter.toFixed(2)}px`);
  root.style.setProperty("--camera-contact-height", `${cameraDiameter.toFixed(2)}px`);
  root.style.setProperty("--camera-blob-x", `${blobX.toFixed(2)}%`);
  root.style.setProperty("--camera-blob-y", `${blobY.toFixed(2)}%`);
  root.style.setProperty("--reflection-opacity", (0.76 - pressure * 0.62).toFixed(3));
  root.style.setProperty("--camera-darkness", (0.18 + cameraResponse * 0.78).toFixed(3));
  root.style.setProperty("--camera-response-opacity", cameraResponse.toFixed(3));
  root.style.setProperty("--coupling-strength", cameraResponse.toFixed(3));
  root.style.setProperty("--annulus-strength", annulusStrength.toFixed(3));
  if (cameraContact) {
    cameraContact.dataset.responseMode = "dark-disk-annular-dimming";
    cameraContact.dataset.annulusStrength = annulusStrength.toFixed(3);
    cameraContact.dataset.contactMaskSignature = contactModel.maskSignature;
    cameraContact.dataset.contactArea = contactModel.area.toFixed(6);
    cameraContact.dataset.contactCentroid = `${contactModel.centerX.toFixed(4)},${contactModel.centerY.toFixed(4)}`;
    cameraContact.dataset.contactShape = `${cameraDiameter.toFixed(2)},${cameraDiameter.toFixed(2)}`;
  }

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

  renderMacro(pressure, contactModel);
  renderMicro2D(pressure, contactModel);
  renderMicro3D(pressure, contactModel);
}

function stopPlayback() {
  isPlaying = false;
  startedAt = 0;
  cancelAnimationFrame(frame);
  clearTimeout(stepTimer);
  stepTimer = 0;
  playButton?.setAttribute("aria-pressed", "false");
  if (playLabel) playLabel.textContent = "Run once";
}

/**
 * Reduced-motion playback: the three interface states in sequence, held
 * briefly, instead of a continuous sweep.
 *
 * Jumping straight to full compression is wrong here. It leaves the button a
 * silent no-op whenever the control is already at full travel, which is the
 * common case right after someone drags the slider to inspect saturation, and
 * even from a lower setting it gives no sign the sequence ran. Discrete steps
 * still avoid the continuous motion this media query is asking us to drop.
 */
const REDUCED_MOTION_STEPS = [0, 0.35, 0.6, 1];
const REDUCED_MOTION_DWELL = 420;

function stepSequence(index) {
  if (!isPlaying) return;
  render(REDUCED_MOTION_STEPS[index]);
  if (index >= REDUCED_MOTION_STEPS.length - 1) {
    stopPlayback();
    return;
  }
  stepTimer = setTimeout(() => stepSequence(index + 1), REDUCED_MOTION_DWELL);
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
  isPlaying = true;
  startedAt = 0;
  playButton?.setAttribute("aria-pressed", "true");
  if (playLabel) playLabel.textContent = "Pause";

  if (reduceMotion.matches) {
    stepSequence(0);
    return;
  }

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
    const currentIndex = microTabs.indexOf(event.currentTarget);
    let targetIndex =
      event.key === "ArrowLeft"
        ? (currentIndex - 1 + microTabs.length) % microTabs.length
        : (currentIndex + 1) % microTabs.length;
    if (event.key === "Home") targetIndex = 0;
    if (event.key === "End") targetIndex = microTabs.length - 1;
    const target = microTabs[targetIndex].id.endsWith("3d") ? "3d" : "2d";
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
