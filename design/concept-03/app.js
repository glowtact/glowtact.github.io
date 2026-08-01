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
const cameraCanvas = document.querySelector("#camera-canvas");
const cameraContext = cameraCanvas?.getContext("2d") ?? null;

const macroGel = document.querySelector(".macro-gel");
const macroTextureLine = document.querySelector(".macro-texture-line");
const macroMembrane = document.querySelector("#macro-membrane");
const macroMembraneShadow = document.querySelector("#macro-membrane-shadow");
const macroAirGap = document.querySelector("#macro-air-gap");
const macroCouplingLine = document.querySelector("#macro-coupling-line");
const macroCouplingGlow = document.querySelector("#macro-coupling-glow");
const macroFieldOfView = document.querySelector("#macro-field-of-view");
const macroFovAxis = document.querySelector("#macro-fov-axis");
const macroCameraAperture = document.querySelector(".macro-camera-aperture");
const macroIndenter = document.querySelector("#macro-indenter");
const macroGapReadout = document.querySelector("#macro-gap-readout");
const macroSpanReadout = document.querySelector("#macro-span-readout");
const macroIndenterReadout = document.querySelector("#macro-indenter-readout");

const microSurfaceFill = document.querySelector("#micro-surface-fill");
const microSvg = document.querySelector("#micro-svg");
const microSurfaceLine = document.querySelector("#micro-surface-line");
const microMembrane = document.querySelector("#micro-membrane");
const microMembraneShadow = document.querySelector("#micro-membrane-shadow");
const microGapArea = document.querySelector("#micro-gap-area");
const microContactPoints = document.querySelector("#micro-contact-points");

const FIELD_SIZE = 61;
const FIELD_ASPERITIES_ACROSS = 12;
const PROFILE_SIZE = 193;
const FIELD_SEED = 2500;
const MACRO_INITIAL_GAP = 18;

/* -------------------------------------------------------------------------
 * Microscopic contact model
 *
 * The section view is solved in dimensionless units: x spans [0, 1] across the
 * sampled window and height is measured in the same arbitrary unit as the
 * asperity heights. Vertical exaggeration is applied only when the profile is
 * mapped to SVG coordinates, which is safe because the Hertz contact width
 *   a = sqrt(R * delta)
 * is invariant under vertical stretching: R scales as 1/k and delta scales as
 * k, so their product is unchanged. The mechanics therefore stay physically
 * proportioned even though the drawing is stretched for legibility.
 * ---------------------------------------------------------------------- */
const PROFILE_ASPERITY_COUNT = 14;
const MICRO_X_START = 28;
const MICRO_X_END = 492;
/** Drawing band: tallest apex sits at the top, deepest valley at the bottom. */
const MICRO_TOP_Y = 112;
const MICRO_FLOOR_Y = 264;
const MICRO_GEL_BOTTOM_Y = 320;
const MICRO_STANDOFF = 0.05;
const MICRO_MAX_INDENTATION = 0.38;
const MICRO_MEMBRANE_THICKNESS = 6;
const MICRO_SAG_MAX = 0.045;
const MICRO_SAG_CURVATURE = 26;
/** Reach of the Hertz edge field, in units of the contact half-width. */
const HERTZ_EDGE_REACH = 2;
/** Amplitude of the 3/2-power departure at the contact edge. */
const HERTZ_EDGE_COEFFICIENT = 0.85;
/** Shoulder length, in units of the contact half-width. */
const SHOULDER_SPAN = 3;
/**
 * Pile-up coefficient: the share of displaced cap area that surfaces as a
 * visible shoulder. It is below one because an axisymmetric asperity also
 * sheds material out of the section plane.
 */
const PILE_UP_COEFFICIENT = 0.32;
const MACRO_MIN_GAP = 1.8;
const INDENTER_CONTACT_PRESSURE = 0.22;
/**
 * Device-scale indentation. At this scale the visible motion is the whole
 * interface being pushed down by the indenter; closing the microscopic gap is
 * a sub-pixel detail that only View B can resolve. Without this the global
 * view barely moved, because the gap travel alone is ~16 user units.
 */
const MACRO_BULK_INDENT = 26;
const MACRO_MEMBRANE_HALF_THICKNESS = 7.5;
const MACRO_INDENTER_BASE_Y = 197;
const MACRO_INDENTER_APPROACH_GAP = 60;
/** Flat part of the indenter face, matching the drawn geometry. */
const MACRO_INDENTER_FACE_HALF_WIDTH = 24;
const MACRO_INDENTATION_DECAY = 105;
const MACRO_FOV_APEX_X = 460;
const MACRO_FOV_APEX_Y = 492;
/** Fixed cone half-angle, so a nearer interface plane gives a smaller footprint. */
const MACRO_FOV_SLOPE = 0.784;
/**
 * Coupling fraction at which the tallest asperity first touches the membrane
 * in the microscopic model. Both views key off it, so the device-scale
 * coupling band and the microscope's first plateau appear at the same instant
 * rather than ~70% of the slider apart.
 */
const MICRO_FIRST_CONTACT_COUPLING =
  MICRO_STANDOFF / (MICRO_STANDOFF + MICRO_MAX_INDENTATION);
const MACRO_COUPLING_GAP =
  MACRO_INITIAL_GAP -
  (MACRO_INITIAL_GAP - MACRO_MIN_GAP) * MICRO_FIRST_CONTACT_COUPLING;
const SVG_NS = "http://www.w3.org/2000/svg";

let activeMicroView = "2d";
let currentPressure = Number(pressureInput?.value ?? 0) / 100;
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

/**
 * Rounded-tip cusp shared by the 2D section and the 3D field: a parabolic cap
 * of radius `tipRadius` blended C1-continuously into a straight flank that
 * reaches the valley floor at `halfWidth`. `tipBluntness` is the cap radius as
 * a fraction of the radius a pure parabola of the same footprint would have,
 * so it sharpens the tip without changing the envelope. Both views run the
 * same contact solve on this shape.
 */
function makeAsperityShape(halfWidth, height, tipBluntness) {
  const parabolicRadius = (halfWidth * halfWidth) / (2 * height);
  return {
    halfWidth,
    height,
    tipRadius: parabolicRadius * tipBluntness,
    capHalfWidth: halfWidth * (1 - Math.sqrt(1 - tipBluntness))
  };
}

function asperityShapeHeight(shape, distance) {
  if (distance >= shape.halfWidth) return 0;
  if (distance <= shape.capHalfWidth) {
    return shape.height - (distance * distance) / (2 * shape.tipRadius);
  }
  const capTop =
    shape.height - (shape.capHalfWidth * shape.capHalfWidth) / (2 * shape.tipRadius);
  const flankSlope = shape.capHalfWidth / shape.tipRadius;
  return Math.max(0, capTop - (distance - shape.capHalfWidth) * flankSlope);
}

/** Hertz contact half-width for a flat plane pressed into the tip by `indentation`. */
function hertzHalfContact(shape, indentation) {
  if (indentation <= 0) return 0;
  let halfContact = Math.sqrt(shape.tipRadius * indentation);
  if (halfContact > shape.capHalfWidth) {
    // Past the rounded cap the flank is nearly straight, so the contact patch
    // widens more slowly than the parabolic law predicts.
    halfContact = shape.capHalfWidth + (halfContact - shape.capHalfWidth) * 0.6;
  }
  return Math.min(halfContact, shape.halfWidth * 0.86);
}

function fieldBaseline(x, y) {
  return (
    0.055 +
    Math.sin(x * Math.PI * 3.1 + 0.7) * 0.02 +
    Math.cos(y * Math.PI * 2.6 + 1.2) * 0.018 +
    Math.sin((x - y) * Math.PI * 2.2) * 0.012
  );
}

function generateFieldAsperities(seed) {
  const random = seededRandom(seed);
  const grid = FIELD_ASPERITIES_ACROSS;
  const asperities = [];

  for (let row = 0; row < grid; row += 1) {
    for (let column = 0; column < grid; column += 1) {
      const halfWidth = (0.44 + random() * 0.26) / grid;
      const height = 0.6 + random() * 0.4;
      const tipBluntness = 0.46 + random() * 0.34;
      const x = (column + 0.26 + random() * 0.48) / grid;
      const y = (row + 0.26 + random() * 0.48) / grid;
      asperities.push({
        x,
        y,
        shape: makeAsperityShape(halfWidth, height, tipBluntness),
        apexHeight: fieldBaseline(x, y) + height
      });
    }
  }

  return asperities;
}

const fieldAsperities = generateFieldAsperities(FIELD_SEED);

function generateSurfaceField(size) {
  return Array.from({ length: size }, (_, row) => {
    const y = row / (size - 1);
    return Array.from({ length: size }, (_, column) => {
      const x = column / (size - 1);
      let peak = 0;
      fieldAsperities.forEach((asperity) => {
        peak = Math.max(
          peak,
          asperityShapeHeight(asperity.shape, Math.hypot(x - asperity.x, y - asperity.y))
        );
      });
      return fieldBaseline(x, y) + peak;
    });
  });
}

const surfaceField = generateSurfaceField(FIELD_SIZE);
const fieldApexMaximum = Math.max(
  ...fieldAsperities.map((asperity) => asperity.apexHeight)
);

function profileBaseline(x) {
  return (
    0.055 +
    Math.sin(x * Math.PI * 3.4 + 0.35) * 0.02 +
    Math.cos(x * Math.PI * 1.7 + 1.1) * 0.014
  );
}

/**
 * Each asperity is a rounded-tip cusp: a parabolic cap of radius `tipRadius`
 * blended C1-continuously into a straight flank that reaches the valley floor
 * at `halfWidth`. `tipBluntness` is the cap radius as a fraction of the radius
 * a pure parabola of the same footprint would have, so it controls how sharp
 * the tip is without changing the asperity envelope.
 */
function generateProfileAsperities(seed) {
  const random = seededRandom(seed);
  const count = PROFILE_ASPERITY_COUNT;

  return Array.from({ length: count }, (_, index) => {
    const halfWidth = (0.44 + random() * 0.26) / count;
    // A broad apex-height spread is what makes contact progressive: the
    // tallest asperities carry load first and the shortest never couple, so
    // real contact area stays well below the nominal area at full load.
    const height = 0.6 + random() * 0.4;
    const tipBluntness = 0.46 + random() * 0.34;
    const parabolicRadius = (halfWidth * halfWidth) / (2 * height);
    const tipRadius = parabolicRadius * tipBluntness;
    const capHalfWidth = halfWidth * (1 - Math.sqrt(1 - tipBluntness));
    const x = (index + 0.26 + random() * 0.48) / count;

    return {
      x,
      halfWidth,
      height,
      tipRadius,
      capHalfWidth,
      apexHeight: profileBaseline(x) + height
    };
  });
}

const profileAsperities = generateProfileAsperities(FIELD_SEED + 17);

function asperityProfileHeight(asperity, offset) {
  const distance = Math.abs(offset);
  if (distance >= asperity.halfWidth) return 0;
  if (distance <= asperity.capHalfWidth) {
    return asperity.height - (distance * distance) / (2 * asperity.tipRadius);
  }
  const capTop =
    asperity.height -
    (asperity.capHalfWidth * asperity.capHalfWidth) / (2 * asperity.tipRadius);
  const flankSlope = asperity.capHalfWidth / asperity.tipRadius;
  return Math.max(0, capTop - (distance - asperity.capHalfWidth) * flankSlope);
}

function undeformedProfileHeight(x) {
  let peak = 0;
  profileAsperities.forEach((asperity) => {
    peak = Math.max(peak, asperityProfileHeight(asperity, x - asperity.x));
  });
  return profileBaseline(x) + peak;
}

const surfaceProfile = Array.from({ length: PROFILE_SIZE }, (_, index) =>
  undeformedProfileHeight(index / (PROFILE_SIZE - 1))
);

const profileApexMaximum = Math.max(
  ...profileAsperities.map((asperity) => asperity.apexHeight)
);
const profileFloorMinimum = Math.min(...surfaceProfile);
/**
 * Height-to-y mapping derived from the generated profile, so the relief always
 * fills the drawing band regardless of the seed. This is the only place the
 * vertical exaggeration is applied; the contact solve stays dimensionless.
 */
const MICRO_HEIGHT_SCALE =
  (MICRO_FLOOR_Y - MICRO_TOP_Y) /
  Math.max(profileApexMaximum - profileFloorMinimum, Number.EPSILON);
const MICRO_BASE_Y = MICRO_FLOOR_Y + profileFloorMinimum * MICRO_HEIGHT_SCALE;

/** Membrane plane over the 3D field, on the same schedule as the 2D section. */
function fieldPlaneFor(couplingPressure) {
  return (
    fieldApexMaximum +
    MICRO_STANDOFF -
    couplingPressure * (MICRO_STANDOFF + MICRO_MAX_INDENTATION)
  );
}

let fieldContactCache = null;

/**
 * Real contact area over the sampled window: a circular Hertz patch per loaded
 * asperity, not the geometric intersection of the surface with the plane. The
 * patch is narrower than that intersection by a factor of sqrt(2), and summing
 * patch areas is what lets the 3D shading and the readout agree — previously
 * the render flooded amber from every peak that merely cleared the plane.
 */
function fieldContactSolve(couplingPressure) {
  const plane = fieldPlaneFor(couplingPressure);
  if (fieldContactCache && fieldContactCache.plane === plane) {
    return fieldContactCache;
  }

  const patches = [];
  let area = 0;
  fieldAsperities.forEach((asperity) => {
    const indentation = asperity.apexHeight - plane;
    const halfContact = hertzHalfContact(asperity.shape, indentation);
    if (halfContact <= 0) return;
    patches.push({ x: asperity.x, y: asperity.y, halfContact, indentation });
    area += Math.PI * halfContact * halfContact;
  });

  fieldContactCache = {
    plane,
    patches,
    // The window is the unit square, so summed patch area is already a fraction.
    fraction: Math.min(area, 1)
  };
  return fieldContactCache;
}

/** Smooth 0..1 coverage of a sample point by any contact patch. */
function fieldContactCoverage(patches, x, y, featherRadius) {
  let coverage = 0;
  for (let index = 0; index < patches.length; index += 1) {
    const patch = patches[index];
    const distance = Math.hypot(x - patch.x, y - patch.y);
    const local = Math.min(
      Math.max((patch.halfContact - distance) / featherRadius + 0.5, 0),
      1
    );
    if (local > coverage) coverage = local;
    if (coverage >= 1) break;
  }
  return coverage;
}

function stateFor(pressure) {
  if (pressure < INDENTER_CONTACT_PRESSURE) {
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

const MAX_FIELD_CONTACT_FRACTION = fieldContactSolve(1).fraction;

/**
 * Height of the membrane's lower face over the sampled window. It starts one
 * standoff above the tallest apex, so an air gap is still open when the
 * indenter first touches the membrane, and descends linearly with coupling.
 */
function membranePlaneFor(couplingPressure) {
  return (
    profileApexMaximum +
    MICRO_STANDOFF -
    couplingPressure * (MICRO_STANDOFF + MICRO_MAX_INDENTATION)
  );
}

/**
 * Qualitative Hertz solve, one asperity at a time. A rigid flat pressed into a
 * parabolic tip by `delta` contacts it over a half-width sqrt(R * delta); the
 * flattened cap material is booked as displaced area and re-emerges as a
 * shoulder outside the contact-affected zone.
 */
function solveAsperityContacts(plane) {
  return profileAsperities.map((asperity) => {
    const indentation = asperity.apexHeight - plane;
    if (indentation <= 0) {
      return {
        asperity,
        indentation: 0,
        halfContact: 0,
        shoulderAmplitude: 0
      };
    }

    let halfContact = Math.sqrt(asperity.tipRadius * indentation);
    if (halfContact > asperity.capHalfWidth) {
      // Past the rounded cap the flank is nearly straight, so the contact
      // patch widens more slowly than the parabolic law predicts.
      halfContact =
        asperity.capHalfWidth + (halfContact - asperity.capHalfWidth) * 0.6;
    }
    halfContact = Math.min(halfContact, asperity.halfWidth * 0.86);

    const steps = 40;
    let displacedArea = 0;
    for (let step = 0; step < steps; step += 1) {
      const offset = -halfContact + ((step + 0.5) / steps) * 2 * halfContact;
      displacedArea += Math.max(
        profileBaseline(asperity.x) +
          asperityProfileHeight(asperity, offset) -
          plane,
        0
      );
    }
    displacedArea *= (2 * halfContact) / steps;

    return {
      asperity,
      indentation,
      halfContact,
      // The raised-cosine shoulder integrates to SHOULDER_SPAN * halfContact
      // per side over both flanks, so this amplitude carries exactly the
      // requested share of the displaced area.
      shoulderAmplitude:
        halfContact > 0
          ? (PILE_UP_COEFFICIENT * displacedArea) /
            (SHOULDER_SPAN * halfContact)
          : 0
    };
  });
}

/**
 * Deformed surface height at x. Inside a contact the surface is exactly the
 * membrane plane, which is what makes the plateau a real flat instead of a
 * decorative bar. Just outside it the surface departs with the 3/2-power Hertz
 * edge asymptote, and further out the pile-up shoulder lifts the far field.
 */
function deformedProfileSample(x, plane, contacts) {
  const base = undeformedProfileHeight(x);
  let ceiling = Infinity;
  let shoulder = 0;
  let coupled = false;

  contacts.forEach((contact) => {
    if (contact.halfContact <= 0) return;
    const distance = Math.abs(x - contact.asperity.x);

    if (distance <= contact.halfContact) {
      coupled = true;
      ceiling = Math.min(ceiling, plane);
      return;
    }

    const edge = distance / contact.halfContact - 1;
    if (edge <= HERTZ_EDGE_REACH) {
      ceiling = Math.min(
        ceiling,
        plane -
          contact.indentation *
            HERTZ_EDGE_COEFFICIENT *
            Math.pow(edge, 1.5)
      );
      return;
    }

    if (edge <= HERTZ_EDGE_REACH + SHOULDER_SPAN) {
      const phase = (edge - HERTZ_EDGE_REACH) / SHOULDER_SPAN;
      shoulder = Math.max(
        shoulder,
        contact.shoulderAmplitude * 0.5 * (1 - Math.cos(2 * Math.PI * phase))
      );
    }
  });

  return { height: Math.min(base + shoulder, ceiling), coupled };
}

/** Distance from x to the nearest contact edge, or Infinity when unloaded. */
function distanceToContact(x, contacts) {
  let nearest = Infinity;
  contacts.forEach((contact) => {
    if (contact.halfContact <= 0) return;
    nearest = Math.min(
      nearest,
      Math.max(Math.abs(x - contact.asperity.x) - contact.halfContact, 0)
    );
  });
  return nearest;
}

function microHeightToY(height) {
  return MICRO_BASE_Y - height * MICRO_HEIGHT_SCALE;
}

function contactRatio(couplingPressure) {
  return fieldContactSolve(couplingPressure).fraction;
}

function couplingPressureFor(pressure) {
  const normalized = Math.min(
    Math.max((pressure - INDENTER_CONTACT_PRESSURE) / (1 - INDENTER_CONTACT_PRESSURE), 0),
    1
  );
  return Math.pow(normalized, 0.75);
}

/**
 * Places the indenter's face on the membrane's upper surface once it has
 * arrived, instead of guessing an offset that left a permanent visible gap
 * between a "touching" indenter and the membrane it is supposed to press.
 */
function indenterYFor(pressure, membraneCenterY) {
  const approach = Math.min(pressure / INDENTER_CONTACT_PRESSURE, 1);
  const contactY = membraneCenterY - MACRO_MEMBRANE_HALF_THICKNESS;
  const restY = contactY - MACRO_INDENTER_APPROACH_GAP * (1 - approach);
  return restY - MACRO_INDENTER_BASE_Y;
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

/**
 * Indentation profile: flat under the indenter's face, then decaying as the
 * membrane and gel are drawn down around it. The previous quartic was almost
 * flat-topped over the whole span, so coupling snapped from nothing to nearly
 * its full width in one step instead of spreading outward.
 */
function macroIndentationWeight(x) {
  const distance = Math.abs(x - MACRO_FOV_APEX_X);
  if (distance <= MACRO_INDENTER_FACE_HALF_WIDTH) return 1;
  return Math.exp(
    -Math.pow(
      (distance - MACRO_INDENTER_FACE_HALF_WIDTH) / MACRO_INDENTATION_DECAY,
      2
    )
  );
}

function renderMacro(pressure) {
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
    // Bulk indentation carries the membrane and the gel surface down together;
    // the gap between them closes on top of that shared motion.
    const surfaceY =
      macroSurfaceY(x) + indentation * couplingPressure * MACRO_BULK_INDENT;
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
  const interfaceY = surfacePoints[centerIndex].y;

  if (macroIndenter) {
    const indenterY = indenterYFor(pressure, membranePoints[centerIndex].y);
    macroIndenter.dataset.contactState =
      pressure >= INDENTER_CONTACT_PRESSURE ? "touching" : "approaching";
    macroIndenter.dataset.distanceToMembrane =
      Math.max(0, INDENTER_CONTACT_PRESSURE - pressure).toFixed(3);
    root.style.setProperty("--indenter-y", `${indenterY.toFixed(2)}px`);
  }

  // The sampled window and the coupling glow ride the interface down with it.
  root.style.setProperty(
    "--interface-shift",
    `${(interfaceY - macroSurfaceY(MACRO_FOV_APEX_X)).toFixed(2)}px`
  );

  if (macroFieldOfView) {
    const halfSpan = MACRO_FOV_SLOPE * (MACRO_FOV_APEX_Y - interfaceY);
    macroFieldOfView.setAttribute(
      "d",
      `M${MACRO_FOV_APEX_X} ${MACRO_FOV_APEX_Y} ` +
        `L${(MACRO_FOV_APEX_X - halfSpan).toFixed(2)} ${interfaceY.toFixed(2)} ` +
        `L${(MACRO_FOV_APEX_X + halfSpan).toFixed(2)} ${interfaceY.toFixed(2)} Z`
    );
    macroFovAxis?.setAttribute(
      "d",
      `M${MACRO_FOV_APEX_X} ${MACRO_FOV_APEX_Y}V${interfaceY.toFixed(2)}`
    );
  }

  let coupledStart = centerIndex;
  let coupledEnd = centerIndex;
  const isCoupled = (index) =>
    surfacePoints[index].y - membranePoints[index].y <= MACRO_COUPLING_GAP;
  if (isCoupled(centerIndex)) {
    while (coupledStart > 0 && isCoupled(coupledStart - 1)) coupledStart -= 1;
    while (coupledEnd < samples - 1 && isCoupled(coupledEnd + 1)) coupledEnd += 1;
  }
  const coupled = isCoupled(centerIndex)
    ? surfacePoints.slice(coupledStart, coupledEnd + 1)
    : [];
  macroCouplingLine?.setAttribute("d", coupled.length > 1 ? smoothPath(coupled) : "");

  const ratio = contactRatio(couplingPressure);
  // Sized from the span that actually satisfies the coupling criterion, so the
  // glow cannot claim a wider coupled region than the geometry supports.
  const coupledHalfSpan =
    coupled.length > 1 ? (coupled[coupled.length - 1].x - coupled[0].x) / 2 : 0;

  if (macroGapReadout) {
    const centerGap =
      surfacePoints[centerIndex].y - membranePoints[centerIndex].y;
    macroGapReadout.value = `${Math.round((centerGap / MACRO_INITIAL_GAP) * 100)}%`;
  }
  if (macroSpanReadout) {
    const fieldHalfSpan = MACRO_FOV_SLOPE * (MACRO_FOV_APEX_Y - interfaceY);
    macroSpanReadout.value = `${Math.round(
      Math.min(coupledHalfSpan / fieldHalfSpan, 1) * 100
    )}%`;
  }
  if (macroIndenterReadout) {
    macroIndenterReadout.value =
      pressure >= INDENTER_CONTACT_PRESSURE ? "Pressing" : "Approaching";
  }
  macroCouplingGlow?.setAttribute("rx", String(Math.max(coupledHalfSpan, 6)));
  macroCouplingGlow?.setAttribute("ry", String(12 + ratio * 30));
  // The field of view is fixed by the optics, so it stays legible at every
  // load; only how much of it is darkened by coupling changes.
  macroFieldOfView?.setAttribute("opacity", (0.42 + ratio * 0.4).toFixed(3));
  macroCameraAperture?.setAttribute("opacity", (0.48 + ratio * 0.52).toFixed(3));
}

function renderMicro2D(pressure) {
  if (!microSurfaceFill || !microMembrane) return;

  const couplingPressure = couplingPressureFor(pressure);
  const plane = membranePlaneFor(couplingPressure);
  const contacts = solveAsperityContacts(plane);
  const span = MICRO_X_END - MICRO_X_START;

  const samples = Array.from({ length: PROFILE_SIZE }, (_, index) => {
    const normalizedX = index / (PROFILE_SIZE - 1);
    const solved = deformedProfileSample(normalizedX, plane, contacts);
    // The membrane rests on every plateau and sags between them. Taking the
    // higher of the sagging plane and the surface keeps contact conformal
    // while making penetration impossible by construction.
    const gapDistance = distanceToContact(normalizedX, contacts);
    const sag = Number.isFinite(gapDistance)
      ? Math.min(
          MICRO_SAG_MAX * couplingPressure,
          MICRO_SAG_CURVATURE * gapDistance * gapDistance
        )
      : 0;
    const membraneHeight = Math.max(plane - sag, solved.height);

    return {
      x: MICRO_X_START + normalizedX * span,
      surfaceY: microHeightToY(solved.height),
      membraneY: microHeightToY(membraneHeight),
      coupled: solved.coupled
    };
  });

  const surfacePoints = samples.map((sample) => ({
    x: sample.x,
    y: sample.surfaceY
  }));
  const membranePoints = samples.map((sample) => ({
    x: sample.x,
    y: sample.membraneY
  }));

  const surfacePath = angularPath(surfacePoints);
  microSurfaceFill.setAttribute(
    "d",
    `${surfacePath} L${MICRO_X_END} ${MICRO_GEL_BOTTOM_Y} L${MICRO_X_START} ${MICRO_GEL_BOTTOM_Y} Z`
  );
  microSurfaceLine?.setAttribute("d", surfacePath);

  const membraneBottomPath = angularPath(membranePoints);
  const membraneBandPath = `${membraneBottomPath} ${[...membranePoints]
    .reverse()
    .map(
      (point) =>
        `L${point.x.toFixed(2)} ${(point.y - MICRO_MEMBRANE_THICKNESS).toFixed(2)}`
    )
    .join(" ")} Z`;
  microMembrane.setAttribute("d", membraneBandPath);
  microMembraneShadow?.setAttribute("d", membraneBottomPath);
  microGapArea?.setAttribute("d", areaBetween(membranePoints, surfacePoints));

  const coupledSamples = samples.filter((sample) => sample.coupled).length;
  const contactThirdCounts = [0, 0, 0];
  samples.forEach((sample, index) => {
    if (!sample.coupled) return;
    contactThirdCounts[Math.min(Math.floor((index * 3) / PROFILE_SIZE), 2)] += 1;
  });
  const minimumClearance = Math.min(
    ...samples.map((sample) => sample.surfaceY - sample.membraneY)
  );
  const coupledFraction = contacts.reduce(
    (total, contact) => total + 2 * contact.halfContact,
    0
  );

  if (microSvg) {
    microSvg.dataset.minimumClearance = minimumClearance.toFixed(6);
    microSvg.dataset.contactSamples = String(coupledSamples);
    microSvg.dataset.contactThirds = contactThirdCounts.join(",");
    microSvg.dataset.coupledFraction = coupledFraction.toFixed(4);
    microSvg.dataset.profileSignature = profileSignature;
  }

  if (!microContactPoints) return;
  microContactPoints.replaceChildren();
  const plateauWidths = [];
  const plateauY = microHeightToY(plane);

  contacts.forEach((contact) => {
    if (contact.halfContact <= 0) return;
    const centerX = MICRO_X_START + contact.asperity.x * span;
    const halfWidth = contact.halfContact * span;
    const left = Math.max(centerX - halfWidth, MICRO_X_START);
    const right = Math.min(centerX + halfWidth, MICRO_X_END);
    if (right - left <= 0) return;

    plateauWidths.push(right - left);
    // Drawn exactly on the flattened plateau, which is also the membrane's
    // lower face there, so the coupled span is part of the geometry rather
    // than a marker floating above an unflattened tip.
    const segment = document.createElementNS(SVG_NS, "path");
    segment.setAttribute("class", "micro-contact-segment");
    segment.setAttribute(
      "d",
      `M${left.toFixed(2)} ${plateauY.toFixed(2)} H${right.toFixed(2)}`
    );
    microContactPoints.append(segment);
  });

  if (microSvg) {
    microSvg.dataset.plateauWidths = plateauWidths
      .map((width) => width.toFixed(2))
      .join(",");
  }
}

/* -------------------------------------------------------------------------
 * Camera response
 *
 * Every pixel is derived, not decorated. The ROI is mapped back onto the
 * device-scale indentation profile; the local indentation sets a local
 * coupling level; that level is run through the same field contact solve as
 * View B to get a local real contact area; and darkening is a function of that
 * area. So the dark region's extent comes from View A and its depth comes from
 * View B, instead of an ellipse that happened to grow with the slider.
 * ---------------------------------------------------------------------- */
const CAMERA_LUT_STEPS = 64;
const CAMERA_FRACTION_LUT = Array.from(
  { length: CAMERA_LUT_STEPS + 1 },
  (_, index) => fieldContactSolve(index / CAMERA_LUT_STEPS).fraction
);

function cameraFractionFor(couplingPressure) {
  const position =
    Math.min(Math.max(couplingPressure, 0), 1) * CAMERA_LUT_STEPS;
  const lower = Math.floor(position);
  const upper = Math.min(lower + 1, CAMERA_LUT_STEPS);
  const blend = position - lower;
  return (
    CAMERA_FRACTION_LUT[lower] * (1 - blend) + CAMERA_FRACTION_LUT[upper] * blend
  );
}

/** Static, seeded sensor grain: fixed-pattern noise, not animated sparkle. */
const CAMERA_GRAIN = (() => {
  const random = seededRandom(FIELD_SEED + 991);
  return Float32Array.from({ length: 4096 }, () => random());
})();

/** Smoothly interpolated coarse lattice for unresolved contact clustering. */
const CAMERA_LATTICE_SIZE = 44;
const CAMERA_LATTICE = (() => {
  const random = seededRandom(FIELD_SEED + 4127);
  return Float32Array.from(
    { length: CAMERA_LATTICE_SIZE * CAMERA_LATTICE_SIZE },
    () => random()
  );
})();

function cameraLatticeNoise(u, v) {
  const x = u * (CAMERA_LATTICE_SIZE - 1);
  const y = v * (CAMERA_LATTICE_SIZE - 1);
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const fx = x - x0;
  const fy = y - y0;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const at = (column, row) =>
    CAMERA_LATTICE[
      Math.min(row, CAMERA_LATTICE_SIZE - 1) * CAMERA_LATTICE_SIZE +
        Math.min(column, CAMERA_LATTICE_SIZE - 1)
    ];
  const top = at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx;
  const bottom = at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx;
  return top * (1 - sy) + bottom * sy;
}

function renderCamera(couplingPressure) {
  if (!cameraCanvas || !cameraContext) return;

  const width = cameraCanvas.width;
  const height = cameraCanvas.height;
  const image = cameraContext.createImageData(width, height);
  const data = image.data;
  const halfWidth = width / 2;
  const halfHeight = height / 2;
  // The ROI spans the camera's footprint on the interface, in macro units.
  const roiHalfSpan = MACRO_FOV_SLOPE * (MACRO_FOV_APEX_Y - 286);

  for (let row = 0; row < height; row += 1) {
    for (let column = 0; column < width; column += 1) {
      const u = (column - halfWidth) / halfWidth;
      const v = ((row - halfHeight) / halfHeight) * (height / width);
      const radius = Math.hypot(u, v) * roiHalfSpan;

      const localCoupling =
        couplingPressure * macroIndentationWeight(MACRO_FOV_APEX_X + radius);
      const localFraction = cameraFractionFor(localCoupling);
      // Two octaves: fine sensor noise plus a smooth coarser scale standing in
      // for clusters of asperity contacts the camera cannot resolve.
      const fineGrain =
        CAMERA_GRAIN[((row * 67 + column * 31) >>> 0) % CAMERA_GRAIN.length];
      const coarseGrain = cameraLatticeNoise(column / width, row / height);
      const grain = fineGrain * 0.34 + coarseGrain * 0.66;

      // Unresolved individual asperity contacts show up as grain in the
      // darkened area, so the patch reads as texture rather than a soft blob.
      const signal =
        Math.pow(
          Math.min(localFraction / MAX_FIELD_CONTACT_FRACTION, 1),
          0.55
        ) * (0.82 + grain * 0.36);

      const illumination = 1 - 0.16 * Math.hypot(u, v) * Math.hypot(u, v);
      const base = 152 * illumination + (grain - 0.5) * 9;
      const level = base * (1 - Math.min(signal, 1) * 0.79);

      const offset = (row * width + column) * 4;
      data[offset] = Math.max(level * 0.94, 0);
      data[offset + 1] = Math.max(level * 1.02, 0);
      data[offset + 2] = Math.max(level * 0.93, 0);
      data[offset + 3] = 255;
    }
  }

  cameraContext.putImageData(image, 0, 0);
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
  const scaleX = (width * 0.9) / (FIELD_SIZE * 2);
  const scaleY = (height * 0.56) / (FIELD_SIZE * 2);
  const heightScale = height * 0.27;
  const originX = width * 0.5;
  const originY = height * 0.32;
  const couplingPressure = couplingPressureFor(pressure);
  const solve = fieldContactSolve(couplingPressure);
  const plane = solve.plane;
  // Feather over one grid cell so sub-cell patches anti-alias instead of
  // snapping to whole facets, which is what made the amber area overstate the
  // reported coupled fraction.
  const feather = 0.6 / (FIELD_SIZE - 1);
  let contactCellCount = 0;
  const contactQuadrants = [0, 0, 0, 0];

  // Flattened plateaus: a vertex inside a contact patch is pressed to exactly
  // the membrane plane, so the tips are visibly truncated rather than glowing.
  const vertexHeight = (row, column) => {
    const x = column / (FIELD_SIZE - 1);
    const y = row / (FIELD_SIZE - 1);
    const height = surfaceField[row][column];
    if (height <= plane) return height;
    return fieldContactCoverage(solve.patches, x, y, feather) > 0.5
      ? plane
      : Math.min(height, plane);
  };

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
        vertexHeight(row, column),
        vertexHeight(row, column + 1),
        vertexHeight(row + 1, column + 1),
        vertexHeight(row + 1, column)
      ];
      const average = heights.reduce((sum, value) => sum + value, 0) / heights.length;
      // Amber weight is the facet's share of real contact area, so the total
      // amber ink on screen equals the coupled fraction in the readout.
      const contactStrength = fieldContactCoverage(
        solve.patches,
        (column + 0.5) / (FIELD_SIZE - 1),
        (row + 0.5) / (FIELD_SIZE - 1),
        feather
      );
      if (contactStrength > 0.5) {
        contactCellCount += 1;
        const quadrant =
          (row >= (FIELD_SIZE - 1) / 2 ? 2 : 0) +
          (column >= (FIELD_SIZE - 1) / 2 ? 1 : 0);
        contactQuadrants[quadrant] += 1;
      }
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

      const depth = Math.min(Math.max((plane - average) / 0.42, 0), 1);
      const tone = Math.round(128 - depth * 74);
      const baseColor = [Math.round(tone * 0.75), tone, Math.round(tone * 0.91)];
      const color = baseColor.map((channel, index) =>
        Math.round(channel + ([255, 186, 58][index] - channel) * contactStrength)
      );
      context.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
      context.strokeStyle =
        contactStrength > 0.02
          ? `rgba(255, 218, 126, ${(0.1 + contactStrength * 0.4).toFixed(3)})`
          : "rgba(210, 228, 220, 0.06)";

      context.fill();
      context.stroke();
    }
  }

  microCanvas.dataset.contactCells = String(contactCellCount);
  microCanvas.dataset.contactQuadrants = contactQuadrants.join(",");
  microCanvas.dataset.fieldSignature = fieldSignature;

  // The membrane's lower face, drawn as a flat sheet at the solved plane. The
  // air gap is everything visible between it and the surface below.
  context.lineWidth = Math.max(pixelRatio * 0.9, 1);
  context.strokeStyle = "rgba(226, 236, 230, 0.16)";
  for (let row = 0; row < FIELD_SIZE; row += 6) {
    context.beginPath();
    for (let column = 0; column < FIELD_SIZE; column += 1) {
      const point = project(column, row, plane);
      if (column === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    }
    context.stroke();
  }
  for (let column = 0; column < FIELD_SIZE; column += 6) {
    context.beginPath();
    for (let row = 0; row < FIELD_SIZE; row += 1) {
      const point = project(column, row, plane);
      if (row === 0) context.moveTo(point.x, point.y);
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
    `${(contactRatio(couplingPressure) * 100).toFixed(1)}% REAL CONTACT AREA / QUALITATIVE`,
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
  const couplingPressure = couplingPressureFor(pressure);
  const ratio = contactRatio(couplingPressure);
  // Normalise against the full coupled-area range the model can reach, not an
  // arbitrary early cut-off. Clamping at a low fraction froze the response
  // over the upper half of the slider while contact was still growing. The
  // gamma keeps the first coupled patches visible without ever flattening out.
  const cameraSignal = Math.pow(
    Math.min(Math.max(ratio / MAX_FIELD_CONTACT_FRACTION, 0), 1),
    0.45
  );

  currentPressure = pressure;
  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--signal-level", `${percent}%`);
  root.style.setProperty("--coupling-width", `${48 + cameraSignal * 162}px`);
  root.style.setProperty("--reflection-opacity", (0.76 - pressure * 0.62).toFixed(3));
  root.style.setProperty("--camera-darkness", (0.18 + cameraSignal * 0.78).toFixed(3));
  root.style.setProperty("--camera-response-opacity", cameraSignal.toFixed(3));

  if (pressureInput) pressureInput.value = String(percent);
  if (pressurePercent) pressurePercent.value = `${percent}%`;
  if (toolbarState) toolbarState.value = state.title;
  if (stateIndex) stateIndex.textContent = state.index;
  if (stateCopy) stateCopy.textContent = state.copy;
  if (contactFraction) contactFraction.value = `${(ratio * 100).toFixed(1)}%`;
  if (cameraIntensity) cameraIntensity.value = state.intensity;
  if (microCanvas) {
    microCanvas.setAttribute(
      "aria-label",
      `3D contact field, ${state.title}. Qualitative real contact area ${(ratio * 100).toFixed(1)} percent.`
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
  renderCamera(couplingPressure);
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
