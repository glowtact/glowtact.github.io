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
const macroMembraneBody = document.querySelector("#macro-membrane-body");
const macroScaleMarker = document.querySelector("#macro-scale-marker");
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
const microMembraneBody = document.querySelector("#micro-membrane-body");
const microGapArea = document.querySelector("#micro-gap-area");
const microContactPoints = document.querySelector("#micro-contact-points");

// 61 samples resolve the 12x12 asperity population: feature radii of
// 0.017-0.045 span 1-2.7 grid cells, so each grit is drawn by several quads
// instead of aliasing in and out of the lattice as it did at 41.
const FIELD_SIZE = 61;
const PROFILE_SIZE = 97;
const FIELD_SEED = 2500;
const MICRO_CLEARANCE = 2.5;
const MACRO_INITIAL_GAP = 18;
const MACRO_MIN_GAP = 1.8;
const INDENTER_CONTACT_PRESSURE = 0.22;

/**
 * Drawn thickness of the 3 mil (~76 um) nitrile membrane in the device view.
 * The schematic exaggerates the ~9 um texture, so no single scale is exact;
 * what must read correctly is the ordering: at 76 um the membrane is thicker
 * than the rest air gap it drapes over, so the band is drawn deeper than
 * MACRO_INITIAL_GAP. The indenter rests on the band's top surface.
 */
const MACRO_MEMBRANE_THICKNESS = 22;

/**
 * Post-contact travel of the indenter, in device-view units.
 *
 * Everything under the indenter has to absorb this travel. The air gap can
 * only surrender MACRO_INITIAL_GAP - MACRO_MIN_GAP of it, so whatever remains
 * has to come from the gel itself yielding. Deriving the gel depression from
 * that balance is what keeps the indenter tip resting on the membrane rather
 * than sinking through a surface that never moves.
 */
const MACRO_INDENTER_TRAVEL = 34;
const MACRO_GEL_DEPTH = MACRO_INDENTER_TRAVEL - (MACRO_INITIAL_GAP - MACRO_MIN_GAP);

/** Centre and half-width of the indented region of the gel. */
const MACRO_INDENT_CENTER = 460;
const MACRO_GEL_WIDTH = 150;

/**
 * Shoulder lobes flanking the indent. XP-565 is effectively incompressible at
 * this scale, so material driven out of the well has to reappear beside it.
 */
const MACRO_SHOULDER_GAIN = 0.16;
const MACRO_SHOULDER_OFFSET = 1.75;
const MACRO_SHOULDER_WIDTH = 0.62;
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
  // P2500 grit averages ~8.4 um across, so a ~100 um window holds roughly a
  // dozen asperities per axis -- and in a molded sandpaper texture the grains
  // ABUT: there is no flat land between them. Pitch sets the count (12x12);
  // the radii are sized so the mean grain diameter matches the ~0.083 pitch,
  // which is what removes the empty basins that made earlier populations read
  // as scattered spikes on a plain.
  const gridSize = 12;
  const asperities = [];

  for (let row = 0; row < gridSize; row += 1) {
    for (let column = 0; column < gridSize; column += 1) {
      const radiusMajor = 0.03 + random() * 0.024;
      const radiusMinor = 0.022 + random() * 0.02;
      const angle = random() * Math.PI;
      const shoulderAngle = random() * Math.PI * 2;
      const shoulderDistance = radiusMajor * (0.35 + random() * 0.65);
      asperities.push({
        // Sandpaper grit is sieve-graded: the size and height dispersion is
        // narrow. The earlier 0.5-1.12 height spread buried the short half of
        // the population in the base relief, which halved the APPARENT grain
        // density even though the count was right. Tight jitter and a raised
        // height floor keep every grain visible, so the drawn density matches
        // the true ~9 um period.
        x: (column + 0.22 + random() * 0.56) / gridSize,
        y: (row + 0.22 + random() * 0.56) / gridSize,
        radiusMajor,
        radiusMinor,
        angle,
        cuspPower: 0.72 + random() * 0.66,
        height: 0.68 + random() * 0.38,
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

const fieldHeights = surfaceField.flat();

/**
 * The section is a genuine slice through the field rather than a separate
 * synthetic profile. The slice row is chosen deterministically as the line
 * whose fraction-above-plane curve best matches the whole field's, scored at
 * the given probe planes. A legibility floor keeps the slice from landing in
 * a featureless valley.
 */
function chooseSectionRow(size, probes, candidates = 360) {
  const fieldCurve = probes.map((plane) => fractionAbove(fieldHeights, plane));
  let bestY = 0.5;
  let bestScore = Infinity;

  for (let index = 0; index < candidates; index += 1) {
    const y = (index + 0.5) / candidates;
    const heights = sampleSection(size, y);
    const peaks = heights.filter((height) => height >= 0.42).length;
    // Require enough asperity material for the section to read as texture.
    if (peaks < 3) continue;

    let score = 0;
    for (let probe = 0; probe < probes.length; probe += 1) {
      const difference =
        fractionAbove(heights, probes[probe]) - fieldCurve[probe];
      score += difference * difference;
    }
    if (score < bestScore) {
      bestScore = score;
      bestY = y;
    }
  }
  return bestY;
}

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

/**
 * Qualitative real-contact-area law.
 *
 * Contact starts on the single highest asperity, accelerates as the bulk of
 * the height distribution is swallowed, then saturates: the membrane cannot
 * reach the deepest valleys, so a residual air fraction always survives. The
 * curve is a logistic in load, which reproduces that slow-fast-slow shape.
 */
const CONTACT_SATURATION = 0.985;
const CONTACT_ONSET = 2;
const CONTACT_BIAS = 1.4;

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

/**
 * Section-row selection, deferred until the plane table exists so the slice
 * can be scored where it will actually be judged: at the membrane planes the
 * pressure sweep visits. Uniform probes over [0,1] wasted most of their
 * weight on planes the law never operates at, and with the denser P2500
 * population the row they picked disagreed with the field by up to 12pp in
 * the working range.
 */
const OPERATING_PLANE_PROBES = (() => {
  const probes = [];
  for (let step = 0; step <= 24; step += 1) {
    const pressure =
      INDENTER_CONTACT_PRESSURE +
      (step / 24) * (1 - INDENTER_CONTACT_PRESSURE);
    const plane = membranePlaneFor(couplingPressureFor(pressure));
    if (plane <= 1) probes.push(plane);
  }
  return probes;
})();

// 720 candidates find the same row as 360: ~7pp worst-case disagreement is
// the variance floor of any genuine 1-D slice through this denser field, not
// a search failure. Keeping the slice honest is worth more than forcing the
// number down with a synthetic profile.
const SECTION_ROW = chooseSectionRow(PROFILE_SIZE, OPERATING_PLANE_PROBES);

/** True heights of the section in the shared roughness scale. */
const sectionHeights = sampleSection(PROFILE_SIZE, SECTION_ROW);
const sectionLow = Math.min(...sectionHeights);
const sectionHigh = Math.max(...sectionHeights);
const sectionSpan = Math.max(sectionHigh - sectionLow, Number.EPSILON);
const surfaceProfile = sectionHeights.map(sectionDisplayHeight);

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

/**
 * Device-scale contact chord, in device-view SVG units, for a given micro
 * coupled-area fraction. This is THE single source for how wide the contact
 * region is at device scale: the device view draws its coupling highlight
 * with it, and the camera view sizes its dark patch from it against
 * CAMERA_VIEW_SPAN. One law, three consistent views.
 */
function contactChordUnits(ratio) {
  return ratio > 0 ? Math.max(10, 14 + Math.sqrt(ratio) * 104) : 0;
}

/**
 * Width of membrane the camera images, in device-view units. 260 units
 * (about a third of the drawn sensor) keeps the full-compression contact
 * patch at ~45% of the frame: clearly dominant, with enough surrounding
 * field that it reads as a patch seen by a camera rather than a zoomed
 * crop of the contact itself.
 */
const CAMERA_VIEW_SPAN = 260;

/** Lowest edge of the #macro-indenter outline in SVG coordinates. */
const MACRO_INDENTER_TIP_Y = 197;

/**
 * Translate that puts the indenter tip exactly on the membrane's top surface
 * at the moment of contact. Derived from the geometry rather than tuned: the
 * old hand-picked base left a constant 8.4px air gap that the previous 13px
 * membrane stroke happened to hide.
 */
const INDENTER_CONTACT_TRANSLATE =
  macroSurfaceY(MACRO_INDENT_CENTER, 0) -
  MACRO_INITIAL_GAP -
  MACRO_MEMBRANE_THICKNESS -
  MACRO_INDENTER_TIP_Y;

function indenterYFor(pressure) {
  const approach = Math.min(pressure / INDENTER_CONTACT_PRESSURE, 1);
  const coupling = couplingPressureFor(pressure);
  // Approach from 29px above; from contact onward the tip tracks the top
  // surface, whose descent rate is MACRO_INDENTER_TRAVEL by construction.
  return (
    INDENTER_CONTACT_TRANSLATE -
    29 * (1 - approach) +
    coupling * MACRO_INDENTER_TRAVEL
  );
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

/**
 * Gel surface displacement, positive downward, normalised to 1 at the centre
 * of the indent. The negative lobes either side are the displaced material
 * welling back up.
 */
function macroGelDisplacement(x) {
  const t = (x - MACRO_INDENT_CENTER) / MACRO_GEL_WIDTH;
  const well = Math.exp(-t * t);
  const flank = (Math.abs(t) - MACRO_SHOULDER_OFFSET) / MACRO_SHOULDER_WIDTH;
  return well - MACRO_SHOULDER_GAIN * Math.exp(-flank * flank);
}

function macroSurfaceY(x, couplingPressure = 0) {
  const rest = 286 + Math.sin(x * 0.061) * 0.9 + Math.sin(x * 0.127 + 0.8) * 0.45;
  return rest + macroGelDisplacement(x) * MACRO_GEL_DEPTH * couplingPressure;
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
    const surfaceY = macroSurfaceY(x, couplingPressure);
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

  // The sampled-window chip marks the interface the microscope watches, so
  // it rides the membrane: centred between the membrane underside and the
  // gel surface at the contact centre, descending with them as the indenter
  // presses in. Its rest centre in the markup is y=286.
  if (macroScaleMarker) {
    const interfaceCenterY =
      (membranePoints[centerIndex].y + surfacePoints[centerIndex].y) / 2;
    macroScaleMarker.setAttribute(
      "transform",
      `translate(0 ${(interfaceCenterY - 286).toFixed(2)})`
    );
  }

  macroGel.setAttribute("d", gelPath);
  macroTextureLine?.setAttribute("d", surfacePath);
  // The membrane band: membranePoints trace the underside (the air-gap
  // boundary the texture couples against); the top surface, which the
  // indenter presses on, rides MACRO_MEMBRANE_THICKNESS above it.
  const membraneTopPoints = membranePoints.map((point) => ({
    x: point.x,
    y: point.y - MACRO_MEMBRANE_THICKNESS
  }));
  macroMembrane.setAttribute("d", membranePath);
  macroMembraneBody?.setAttribute(
    "d",
    areaBetween(membraneTopPoints, membranePoints)
  );
  macroMembraneShadow?.setAttribute("d", smoothPath(membraneTopPoints));
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
  // The device-scale contact patch is centred under the indenter, so it is
  // symmetric about it. contactModel.centerX is the centroid of the ~100 um
  // sampled window -- a micro-scale detail of where asperities happen to
  // cluster, which must not translate the macro patch. Driving the chord from
  // it slid the highlight up to 19 units off the indenter and made it wander
  // non-monotonically with pressure.
  const centerX = MACRO_INDENT_CENTER;
  // The 92-unit cap that used to sit here made the device view stop growing
  // while the camera patch (same law, uncapped) kept widening -- the two
  // views disagreed above ~60% pressure.
  const contactChordWidth = contactChordUnits(ratio);
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
      y: macroSurfaceY(point.x - halfChord, couplingPressure)
    });
    contactChord.push({
      x: point.x + halfChord,
      y: macroSurfaceY(point.x + halfChord, couplingPressure)
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

  // The glow marks the coupled interface, so it has to ride the membrane down
  // as the gel yields rather than staying at its rest height.
  macroCouplingGlow?.setAttribute("cx", String(MACRO_INDENT_CENTER));
  macroCouplingGlow?.setAttribute(
    "cy",
    membranePoints[centerIndex].y.toFixed(2)
  );
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
  /*
   * Standoff between the drawn membrane and the surfaces it rests on.
   * Coupling IS the membrane touching the gel, so a fixed 2.5px gap at every
   * pressure drew a continuous air line across the section even at 99%
   * coupled -- the picture contradicted the readout. The full standoff now
   * survives only while coupling is scarce (it keeps the two lines legible
   * at first touch) and closes to a hairline as the coupled fraction grows.
   */
  const contactStandoff =
    MICRO_CLEARANCE * (1 - contactModel.area) + 0.5 * contactModel.area;
  const compliancePenalty = 0.004 + pressure * 0.016;
  const envelope = surfacePoints.map((point, index) => {
    const xNormal = index / (surfacePoints.length - 1);
    const planeY = desiredY + (xNormal - 0.5) * 2.5;
    return contactConstraints.reduce((membraneY, constraint) => {
      const distance = point.x - constraint.x;
      const constraintY =
        constraint.y - contactStandoff + distance * distance * compliancePenalty;
      return Math.min(membraneY, constraintY);
    }, planeY);
  });
  const clearanceLimits = surfacePoints.map(
    (point) => point.y - contactStandoff
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
  // Clearance is only meaningful where the membrane has NOT coupled: over
  // contact the two surfaces coincide by definition. Report the minimum over
  // uncoupled samples so the legibility guarantee applies to the air gap the
  // section actually claims to show.
  const minimumClearance = surfacePoints.reduce((minimum, point, index) => {
    if (contactIndentations[index] > 0) return minimum;
    return Math.min(minimum, point.y - membranePoints[index].y);
  }, Infinity);
  const reportedClearance = Number.isFinite(minimumClearance)
    ? minimumClearance
    : MICRO_CLEARANCE;

  if (microSvg) {
    microSvg.dataset.minimumClearance = reportedClearance.toFixed(6);
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
  // At this zoom a 3 mil (~76 um) membrane is a slab, not a skin: the sampled
  // window is ~100 um wide, so the membrane's far side lies well outside the
  // frame. Fill from the draped underside up past the top edge of the panel;
  // the crop is the honest rendering of its thickness at this scale.
  microMembraneBody?.setAttribute(
    "d",
    areaBetween(membranePoints, [
      { x: 28, y: -12 },
      { x: 492, y: -12 }
    ])
  );
  microGapArea?.setAttribute("d", areaBetween(membranePoints, surfacePoints));

  if (!microContactPoints) return;
  microContactPoints.replaceChildren();
  let run = [];
  const plateauWidths = [];
  const contactCapWidths = [];
  const contactFootprintWidths = [];
  /*
   * One amber path per CONTACT RUN, tracing the flattened surface for the
   * run's full extent. The old rendering drew a small (max 24px) cap at each
   * peak inside the run, so at high pressure -- when contact is a nearly
   * continuous plateau -- the highlight showed a row of beads over a surface
   * that was drawn pressed flat, and its total extent could never match the
   * LOCAL WINDOW percentage. The highlighted length now IS the coupled
   * length: the sum of run widths over the section width tracks the coupled
   * fraction by construction.
   */
  const sampleSpacing = 464 / (PROFILE_SIZE - 1);
  const appendContactRun = () => {
    if (!run.length) return;
    // Each sample owns one spacing-wide cell; summing endpoint differences
    // instead under-counted every run by one cell (a fencepost per run,
    // ~12pp across a fragmented mid-pressure state).
    const width = run[run.length - 1].x - run[0].x + sampleSpacing;
    const drawnWidth = width;
    const maxIndentation = run.reduce(
      (maximum, point) => Math.max(maximum, contactIndentations[point.index]),
      0
    );
    const capCurvature = Math.min(1.1 + maxIndentation * 6.2, 3.4);
    const lift = 1.2;
    let d = "";
    const half = sampleSpacing / 2;
    const first = run[0];
    const last = run[run.length - 1];
    const inner = run
      .map((point) => `L${point.x.toFixed(2)} ${(point.y - lift).toFixed(2)}`)
      .join(" ");
    d = `M${(first.x - half).toFixed(2)} ${(first.y - lift).toFixed(2)} ` +
        inner +
        ` L${(last.x + half).toFixed(2)} ${(last.y - lift).toFixed(2)}`;
    plateauWidths.push(drawnWidth);
    contactCapWidths.push(drawnWidth);
    contactFootprintWidths.push(drawnWidth);
    const contact = document.createElementNS(SVG_NS, "path");
    contact.setAttribute("class", "micro-contact-segment");
    contact.dataset.capCurvature = capCurvature.toFixed(3);
    contact.dataset.capWidth = drawnWidth.toFixed(2);
    contact.dataset.footprintWidth = drawnWidth.toFixed(2);
    contact.setAttribute("d", d);
    microContactPoints.append(contact);
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
  /*
   * How present the membrane lattice is. It marks a plane hovering above the
   * texture; as coupling completes there is no gap left to hover in, so both
   * the grid rules and the uncoupled cell edges fade with it.
   */
  const membraneVisibility = Math.max(0, 1 - contactModel.area * 1.05);

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
      // One blend drives BOTH the flattening and the amber, and it is the
      // cell's coupled fraction EXACTLY. A gamma was tried here to make the
      // coupling read larger, but it made the drawn amber systematically
      // exceed the stated percentage -- the readout said 51% while the ink
      // covered ~60%, and the estimate read as wrong. The drawn fraction now
      // equals the reported fraction by construction; any desire for more
      // coupling belongs in the contact law, where the number and the
      // picture grow together.
      const flattenBlend = contactCoverage;
      const flattenedHeights = heights.map((surfaceHeight) => {
        if (contactStrength <= 0) {
          return surfaceHeight;
        }
        // The membrane plane is impenetrable, so deformation is TRUNCATION:
        // whatever rises above the plane is sliced off at the plane, and the
        // grain's flanks below it stay exactly where they were. The earlier
        // blend shrank the whole grain toward the plane instead, which made
        // partially coupled grains look uniformly melted rather than
        // flat-topped. Truncation happens per vertex, so a grain whose tip
        // crosses the plane shows a flat cap while its shoulders keep their
        // full relief -- the classic asperity-contact picture.
        return Math.min(surfaceHeight, threshold - 0.004);
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
      // Same blend as the geometry: flattened extent and amber extent agree.
      const contactMix = flattenBlend;
      const color = baseColor.map((channel, index) =>
        Math.round(channel + ([227, 161, 40][index] - channel) * contactMix)
      );
      context.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
      // Coupled edges stroke in full-saturation amber; the old pale tint
      // measurably diluted the field at high coupling. Uncoupled edges fade
      // with the membrane grid, since at near-complete contact the lattice
      // has nothing left to delineate.
      context.strokeStyle = contactStrength
        ? `rgba(244, 184, 64, ${0.16 + contactStrength * 0.34})`
        : `rgba(210, 228, 220, ${(0.07 * membraneVisibility).toFixed(3)})`;

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

  // After flattening, no drawn material rises above the membrane plane, so
  // the membrane grid rides the plane itself. The old drape over REST-height
  // peaks floated it over grains that are now drawn pressed flat.
  const membraneHeight = Math.max(threshold + 0.006, 0.03);
  context.lineWidth = Math.max(pixelRatio, 1);
  /*
   * Fade the membrane grid out as coupling completes. These dark rules are
   * drawn across the whole field, so at high coupling they sat on top of the
   * gold sheet and ate into it: with the model reporting 98.5% coupled area
   * the rendered amber measured only 90.9%, which is exactly the mismatch
   * between the picture and the stated percentage. Physically the grid marks
   * a membrane plane hovering above the texture -- once the membrane is
   * pressed home almost everywhere there is no gap left for it to hover in,
   * so it should disappear rather than overlay the contact it has made.
   */
  context.strokeStyle = `rgba(4, 6, 5, ${(0.48 * membraneVisibility).toFixed(3)})`;
  for (let row = 0; row < FIELD_SIZE; row += 4) {
    context.beginPath();
    for (let column = 0; column < FIELD_SIZE; column += 1) {
      const point = project(column, row, membraneHeight);
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
  /*
   * Size the contact region as a PERCENTAGE of the sensor frame, not in
   * pixels. The old pixel value was tuned for one panel size and then
   * clamped at 180px, so at full compression the disc covered barely half
   * the frame while the readout claimed 99% coupled. A share of the frame
   * scales with the layout and lets the region reach the edges when the
   * whole window is in contact. sqrt(area) maps coupled AREA to a diameter.
   */
  /*
   * The camera images the DEVICE view, not the ~100 um microscope window:
   * its dark region is the contact patch under the indenter as seen across
   * the sensor's field of view. Driving the blob from the micro coupled
   * fraction zoomed it until it swallowed the frame at full compression.
   * It now shares the device view's contact-chord law (14 + sqrt(area)*104
   * SVG units) against the ~180-unit membrane span the camera watches, so
   * the tactile image and the global mechanism view stay in proportion:
   * at full compression the patch spans ~65% of the frame, exactly like
   * the chord under the indenter.
   */
  const cameraSpan =
    ratio > 0
      ? Math.max(8, (contactChordUnits(ratio) / CAMERA_VIEW_SPAN) * 100)
      : 7;
  const annulusStrength = 0.12 + cameraResponse * 0.42;

  currentPressure = pressure;
  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--signal-level", `${percent}%`);
  root.style.setProperty("--coupling-width", `${48 + cameraResponse * 162}px`);
  root.style.setProperty("--camera-contact-span", `${cameraSpan.toFixed(2)}%`);
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
    cameraContact.dataset.contactShape = `${cameraSpan.toFixed(2)},${cameraSpan.toFixed(2)}`;
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
