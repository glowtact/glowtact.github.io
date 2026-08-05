from pathlib import Path
import base64
import os
import re
import sys

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


BASE_URL = os.environ.get("GLOWTACT_BASE_URL", "http://127.0.0.1:4173")
ROUTES = {
    "review": "/",
    "optical": "/concept-01/",
    "atlas": "/concept-02/",
    "signal": "/concept-03/",
}
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "mobile": {"width": 390, "height": 844},
}
OUTPUT = Path(
    os.environ.get(
        "GLOWTACT_REVIEW_OUTPUT",
        str(Path(os.environ.get("TEMP", ".")) / "glowtact-review"),
    )
)
MODE = os.environ.get("GLOWTACT_CHECK_MODE", "all")
TRANSPARENT_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
)


def collect_runtime_issues(page: Page) -> list[str]:
    issues: list[str] = []
    page.on("pageerror", lambda error: issues.append(f"pageerror: {error}"))
    page.on(
        "console",
        lambda message: issues.append(f"console {message.type}: {message.text}")
        if message.type == "error"
        else None,
    )
    page.on(
        "response",
        lambda response: issues.append(
            f"HTTP {response.status}: {response.url}"
        )
        if response.status >= 400
        else None,
    )
    return issues


def block_media(page: Page) -> None:
    def handle(route) -> None:
        if route.request.resource_type == "image":
            route.fulfill(
                status=200,
                content_type="image/gif",
                body=TRANSPARENT_GIF,
            )
            return
        if route.request.resource_type in {"media", "font"}:
            route.fulfill(status=204, body=b"")
            return
        route.continue_()

    page.route("**/*", handle)


def navigate(page: Page, path: str, wait_for_images: bool = False):
    response = page.goto(
        f"{BASE_URL}{path}",
        wait_until="domcontentloaded",
        timeout=15_000,
    )
    if wait_for_images:
        page.wait_for_function(
            """() => [...document.images].every(
                image => image.complete && image.naturalWidth > 0
            )""",
            timeout=15_000,
        )
    try:
        page.wait_for_load_state("networkidle", timeout=2_000)
    except PlaywrightTimeoutError:
        ready_state = page.evaluate("() => document.readyState")
        if ready_state not in {"interactive", "complete"}:
            raise
    page.wait_for_timeout(150)
    return response


def assert_layout(page: Page, route_name: str, viewport_name: str) -> None:
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    if overflow > 1:
        offenders = page.evaluate(
            """() => [...document.querySelectorAll('body *')]
                .map(element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        tag: element.tagName,
                        className: String(element.className || ''),
                        parentClass: String(element.parentElement?.className || ''),
                        text: String(element.textContent || '').trim().slice(0, 80),
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                        width: Math.round(rect.width)
                    };
                })
                .filter(item => item.right > innerWidth + 1 || item.left < -1)
                .sort((a, b) => b.right - a.right)
                .slice(0, 8)"""
        )
        scroll_offenders = page.evaluate(
            """() => [...document.querySelectorAll('body *')]
                .map(element => ({
                    tag: element.tagName,
                    className: String(element.className || ''),
                    text: String(element.textContent || '').trim().slice(0, 60),
                    clientWidth: element.clientWidth,
                    scrollWidth: element.scrollWidth
                }))
                .filter(item => item.scrollWidth > item.clientWidth + 1)
                .sort((a, b) => (b.scrollWidth - b.clientWidth) - (a.scrollWidth - a.clientWidth))
                .slice(0, 8)"""
        )
        raise AssertionError(
            f"{route_name}/{viewport_name}: horizontal overflow {overflow}px; "
            f"offenders={offenders}; scroll_offenders={scroll_offenders}"
        )
    h1_count = page.locator("h1").count()
    if h1_count != 1:
        raise AssertionError(
            f"{route_name}/{viewport_name}: expected one h1, found {h1_count}"
        )
    body_text = page.locator("body").inner_text()
    if len(body_text.strip()) < 300:
        raise AssertionError(f"{route_name}/{viewport_name}: page text is incomplete")


def activate_reveals(page: Page) -> None:
    page_height = page.evaluate("() => document.documentElement.scrollHeight")
    viewport_height = page.viewport_size["height"]
    step = max(viewport_height // 2, 320)
    for position in range(0, page_height + step, step):
        page.evaluate("(y) => window.scrollTo(0, y)", position)
        page.wait_for_timeout(45)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(350)


def check_route(
    browser, route_name: str, path: str, viewport_name: str, viewport: dict[str, int]
) -> None:
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    issues = collect_runtime_issues(page)
    response = navigate(page, path, wait_for_images=True)
    if response is None or not response.ok:
        raise AssertionError(f"{route_name}: navigation failed")
    assert_layout(page, route_name, viewport_name)
    activate_reveals(page)
    page.screenshot(
        path=str(OUTPUT / f"{route_name}-{viewport_name}.png"),
        full_page=True,
    )
    if issues:
        raise AssertionError(f"{route_name}/{viewport_name}: {'; '.join(issues)}")
    context.close()


def check_optical_interactions(browser) -> None:
    page = browser.new_page(viewport=VIEWPORTS["desktop"])
    block_media(page)
    issues = collect_runtime_issues(page)
    navigate(page, "/concept-01/")
    pressure = page.locator("#pressure")
    pressure.fill("100")
    if page.locator("#pressure-state").inner_text() != "Expanded coupling":
        raise AssertionError("optical: pressure output did not update")
    page.get_by_role("button", name="Flat").click()
    if (
        page.get_by_role("button", name="Flat").get_attribute("aria-pressed")
        != "true"
    ):
        raise AssertionError("optical: flat probe did not activate")
    page.get_by_role("button", name="Reset mechanism").click()
    if page.locator("#pressure-state").inner_text() != "Air gap":
        raise AssertionError("optical: reset did not restore air gap")
    if issues:
        raise AssertionError(f"optical interactions: {'; '.join(issues)}")
    page.close()


def check_atlas_interactions(browser) -> None:
    page = browser.new_page(viewport=VIEWPORTS["desktop"])
    block_media(page)
    issues = collect_runtime_issues(page)
    navigate(page, "/concept-02/")
    page.locator("#lens-position").fill("80")
    if page.locator("#lens-output").inner_text() != "80%":
        raise AssertionError("atlas: comparison lens did not update")
    page.get_by_role("button", name="03 Tactile").click()
    if page.locator("#layer-title").inner_text() != "Tactile output":
        raise AssertionError("atlas: tactile layer did not activate")
    page.get_by_role("button", name="02 Phillips head Recessed profile").click()
    if page.locator("#specimen-title").inner_text() != "Phillips head":
        raise AssertionError("atlas: Phillips specimen did not activate")
    if "Phillips" not in (page.locator("#specimen-image").get_attribute("alt") or ""):
        raise AssertionError("atlas: specimen alt text did not update")
    if issues:
        raise AssertionError(f"atlas interactions: {'; '.join(issues)}")
    page.close()


def element_center(page: Page, selector: str) -> tuple[float, float]:
    box = page.locator(selector).bounding_box()
    if box is None:
        raise AssertionError(f"signal: {selector} has no rendered bounding box")
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def assert_centered(
    page: Page, subject: str, container: str, tolerance: float = 1.0
) -> None:
    snapshot = page.evaluate(
        """([subjectSelector, containerSelector]) => {
            const subjects = document.querySelectorAll(subjectSelector);
            const containers = document.querySelectorAll(containerSelector);
            if (subjects.length !== 1) {
                return {
                    error: "count",
                    selector: subjectSelector,
                    count: subjects.length,
                };
            }
            if (containers.length !== 1) {
                return {
                    error: "count",
                    selector: containerSelector,
                    count: containers.length,
                };
            }
            const subject = subjects[0];
            const container = containers[0];
            const subjectRect = subject.getBoundingClientRect();
            const containerRect = container.getBoundingClientRect();
            for (const [selector, rect] of [
                [subjectSelector, subjectRect],
                [containerSelector, containerRect],
            ]) {
                if (rect.width <= 0 || rect.height <= 0) {
                    return {
                        error: "bounds",
                        selector,
                        width: rect.width,
                        height: rect.height,
                    };
                }
            }
            return {
                subject: {
                    x: subjectRect.x + subjectRect.width / 2,
                    y: subjectRect.y + subjectRect.height / 2,
                },
                container: {
                    x: containerRect.x + containerRect.width / 2,
                    y: containerRect.y + containerRect.height / 2,
                },
            };
        }""",
        [subject, container],
    )
    if snapshot.get("error") == "count":
        raise AssertionError(
            f"signal: expected one {snapshot['selector']}, "
            f"found {snapshot['count']}"
        )
    if snapshot.get("error") == "bounds":
        raise AssertionError(
            f"signal: {snapshot['selector']} has non-positive rendered bounds "
            f"{snapshot['width']:.2f}x{snapshot['height']:.2f}"
        )
    subject_x = snapshot["subject"]["x"]
    subject_y = snapshot["subject"]["y"]
    container_x = snapshot["container"]["x"]
    container_y = snapshot["container"]["y"]
    delta_x = abs(subject_x - container_x)
    delta_y = abs(subject_y - container_y)
    if delta_x > tolerance or delta_y > tolerance:
        raise AssertionError(
            f"signal: {subject} is not centered in {container}; "
            f"subject=({subject_x:.2f}, {subject_y:.2f}), "
            f"container=({container_x:.2f}, {container_y:.2f}), "
            f"delta=({delta_x:.2f}, {delta_y:.2f}), tolerance={tolerance:.2f}"
        )


def assert_horizontally_centered(
    page: Page, subject: str, container: str, tolerance: float = 1.0
) -> None:
    subject_x, _ = element_center(page, subject)
    container_x, _ = element_center(page, container)
    delta_x = abs(subject_x - container_x)
    if delta_x > tolerance:
        raise AssertionError(
            f"signal: {subject} is not horizontally centered in {container}; "
            f"subject_x={subject_x:.2f}, container_x={container_x:.2f}, "
            f"delta_x={delta_x:.2f}, tolerance={tolerance:.2f}"
        )


def assert_box_height_at_most(
    page: Page, selector: str, maximum: float, label: str
) -> None:
    box = page.locator(selector).bounding_box()
    if box is None:
        raise AssertionError(f"{label}: {selector} has no rendered bounding box")
    if box["height"] > maximum:
        raise AssertionError(
            f"{label}: {selector} is too tall for desktop review; "
            f"height={box['height']:.2f}px, maximum={maximum:.2f}px"
        )


def parse_rgb_triplet(value: str) -> tuple[int, int, int]:
    match = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value)
    if match is None:
        raise AssertionError(f"could not parse rgb color from {value!r}")
    return tuple(int(channel) for channel in match.groups())


def assert_scale_label(page: Page, selector: str, value: int) -> None:
    locator = page.locator(selector)
    count = locator.count()
    if count != 1:
        raise AssertionError(f"signal: expected one {selector}, found {count}")
    if not locator.is_visible():
        raise AssertionError(f"signal: {selector} is not visible")
    label = " ".join((locator.text_content() or "").split())
    pattern = rf"(?<!\d){value}\s*(?:u|µ|μ)\s*m(?![a-z0-9])"
    if re.search(pattern, label, flags=re.IGNORECASE) is None:
        raise AssertionError(
            f"signal: {selector} does not include {value} um; found {label!r}"
        )


def contact_thirds(page: Page) -> set[int]:
    panel_box = page.locator("#micro-svg").bounding_box()
    if panel_box is None:
        raise AssertionError("signal: #micro-svg has no rendered bounding box")
    panel_width = panel_box["width"]
    if panel_width <= 0:
        raise AssertionError(
            f"signal: #micro-svg has non-positive rendered width {panel_width}"
        )
    panel_left = panel_box["x"]
    panel_right = panel_left + panel_width
    thirds: set[int] = set()
    segments = page.locator(".micro-contact-segment")
    for index in range(segments.count()):
        segment_box = segments.nth(index).bounding_box()
        if segment_box is None:
            raise AssertionError(
                f"signal: .micro-contact-segment[{index}] has no rendered bounding box"
            )
        center = segment_box["x"] + segment_box["width"] / 2
        if center < panel_left or center > panel_right:
            raise AssertionError(
                f"signal: .micro-contact-segment[{index}] center {center:.2f} is "
                f"outside #micro-svg bounds [{panel_left:.2f}, {panel_right:.2f}]"
            )
        offset = center - panel_left
        if offset < panel_width / 3:
            thirds.add(0)
        elif offset < panel_width * 2 / 3:
            thirds.add(1)
        else:
            thirds.add(2)
    return thirds


def check_signal_interactions(browser) -> None:
    context = browser.new_context(
        viewport=VIEWPORTS["desktop"], device_scale_factor=2
    )
    page = context.new_page()
    block_media(page)
    issues = collect_runtime_issues(page)
    navigate(page, "/concept-03/")

    for selector in (
        ".macro-camera-lens",
        "#macro-field-of-view",
        ".macro-scale-marker",
        ".macro-interface-note",
    ):
        count = page.locator(selector).count()
        if count != 1:
            raise AssertionError(f"signal: expected one {selector}, found {count}")
        box = page.locator(selector).bounding_box()
        if box is None or box["width"] <= 0 or box["height"] <= 0:
            raise AssertionError(
                f"signal: {selector} has no non-empty rendered bounding box"
            )
    assert_scale_label(page, ".macro-interface-note", 9)
    assert_scale_label(page, ".micro-window-label", 100)

    assert_horizontally_centered(
        page, "#macro-indenter", ".macro-stage svg"
    )
    assert_horizontally_centered(
        page, ".macro-camera-lens", ".macro-stage svg"
    )

    micro_2d = page.locator("#micro-tab-2d")
    micro_3d = page.locator("#micro-tab-3d")
    panel_2d = page.locator("#micro-panel-2d")
    panel_3d = page.locator("#micro-panel-3d")
    pressure = page.locator("#signal-pressure")
    if page.locator("#pressure-percent").inner_text() != "0%":
        raise AssertionError("signal: default pressure is not 0%")
    if page.locator("#camera-intensity").inner_text() != "No signal":
        raise AssertionError("signal: default camera response is not gated off")
    if page.locator(".camera-reference").count() != 1:
        raise AssertionError("signal: missing realistic camera response reference layer")
    camera_stage_box = page.locator(".camera-stage").bounding_box()
    if camera_stage_box is None:
        raise AssertionError("signal: camera stage has no rendered box")
    camera_aspect = camera_stage_box["width"] / camera_stage_box["height"]
    if abs(camera_aspect - (4 / 3)) > 0.08:
        raise AssertionError(
            f"signal: camera ROI aspect ratio {camera_aspect:.3f} is not close to 4:3"
        )
    camera_reference_style = page.locator(".camera-reference").evaluate(
        "element => { const style = getComputedStyle(element); return { image: style.backgroundImage, size: style.backgroundSize }; }"
    )
    if "camera-response-screw-cross.png" in camera_reference_style["image"] and "cover" in camera_reference_style["size"]:
        raise AssertionError("signal: camera response directly enlarges the tactile reference image")
    default_opacity = float(
        page.locator(".camera-contact").evaluate(
            "element => getComputedStyle(element).opacity"
        )
    )
    if default_opacity > 0.05:
        raise AssertionError(
            f"signal: camera contact should be hidden at 0%, opacity {default_opacity}"
        )
    camera_stage_color = parse_rgb_triplet(
        page.locator(".camera-stage").evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
    )
    if sum(camera_stage_color) / 3 > 150:
        raise AssertionError(
            f"signal: no-contact camera field is too bright: {camera_stage_color}"
        )
    initial_gap = page.locator("#macro-air-gap").get_attribute(
        "data-center-clearance"
    )
    if initial_gap is None:
        raise AssertionError("signal: macro center air-gap metric is missing")
    if not 10 <= float(initial_gap) <= 22:
        raise AssertionError(f"signal: initial macro air gap is not small: {initial_gap}")
    if page.locator("#macro-indenter").get_attribute("data-contact-state") != "approaching":
        raise AssertionError("signal: indenter should start above the membrane")
    assert_box_height_at_most(
        page, ".mechanism-shell", 920, "signal"
    )
    font_families = page.evaluate(
        """() => [...document.querySelectorAll('body *')]
            .filter(element => element.getBoundingClientRect().width > 0)
            .map(element => getComputedStyle(element).fontFamily.split(',')[0].replaceAll('"', '').trim())
            .filter(Boolean)"""
    )
    primary_families = {
        family for family in font_families
        if not family.lower().startswith(("sans", "monospace"))
    }
    if len(primary_families) > 2:
        raise AssertionError(
            f"signal: expected at most two primary font families, found {sorted(primary_families)}"
        )
    fov_style = page.locator("#macro-field-of-view").evaluate(
        "element => ({ stroke: getComputedStyle(element).stroke, fill: getComputedStyle(element).fill })"
    )
    fov_label = " ".join(
        (page.locator(".macro-fov text").text_content() or "").split()
    )
    if fov_label != "CAMERA FOV GUIDE":
        raise AssertionError(f"signal: unclear FOV label {fov_label!r}")
    fov_stroke = parse_rgb_triplet(fov_style["stroke"])
    if fov_stroke[0] > 200 and fov_stroke[1] > 140 and fov_stroke[2] < 100:
        raise AssertionError(
            f"signal: camera FOV triangle still reads as amber coupling highlight: {fov_style}"
        )

    pressure.fill("20")
    precontact_opacity = float(
        page.locator(".camera-contact").evaluate(
            "element => getComputedStyle(element).opacity"
        )
    )
    if precontact_opacity > 0.05:
        raise AssertionError(
            f"signal: camera response appeared before membrane contact: {precontact_opacity}"
        )

    if micro_2d.get_attribute("aria-selected") != "true":
        raise AssertionError("signal: 2D microscope is not selected by default")
    if panel_2d.is_hidden() or not panel_3d.is_hidden():
        raise AssertionError("signal: default microscope panel visibility is incorrect")

    representative_pressures = (0, 25, 55, 75, 100)
    dense_pressures = sorted(set(range(0, 101, 5)) | {2, 15, 16})
    contact_samples = []
    profile_signature = None
    for pressure_value in dense_pressures:
        pressure.fill(str(pressure_value))
        assert_centered(page, ".camera-contact", ".camera-stage")
        minimum_clearance = page.locator("#micro-svg").get_attribute(
            "data-minimum-clearance"
        )
        if minimum_clearance is None:
            raise AssertionError("signal: 2D minimum-clearance metric is missing")
        if float(minimum_clearance) < 2.5 - 1e-6:
            raise AssertionError(
                f"signal: 2D clearance {minimum_clearance} is below 2.5 "
                f"at {pressure_value}% pressure"
            )
        signature = page.locator("#micro-svg").get_attribute(
            "data-profile-signature"
        )
        if not signature:
            raise AssertionError("signal: 2D profile signature is missing")
        if profile_signature is None:
            profile_signature = signature
        elif signature != profile_signature:
            raise AssertionError("signal: 2D profile changed across pressure renders")
        if pressure_value in representative_pressures:
            sample_count = page.locator("#micro-svg").get_attribute(
                "data-contact-samples"
            )
            if sample_count is None:
                raise AssertionError("signal: 2D contact-sample metric is missing")
            contact_samples.append(int(sample_count))
        if pressure_value == 35:
            if page.locator("#macro-indenter").get_attribute("data-contact-state") != "touching":
                raise AssertionError("signal: indenter did not reach membrane before camera response")
            page.wait_for_timeout(140)
            response_opacity = float(
                page.locator(".camera-contact").evaluate(
                    "element => getComputedStyle(element).opacity"
                )
            )
            if response_opacity <= 0.12:
                raise AssertionError(
                    "signal: camera response did not appear after coupling began"
                )
    if contact_samples != sorted(contact_samples):
        raise AssertionError(
            f"signal: 2D contact samples are not monotonic: {contact_samples}"
        )

    pressure.fill("55")
    thirds = contact_thirds(page)
    if thirds != {0, 1, 2}:
        raise AssertionError(
            f"signal: contact segments do not span all thirds; found {sorted(thirds)}"
        )
    third_counts_value = page.locator("#micro-svg").get_attribute(
        "data-contact-thirds"
    )
    if third_counts_value is None:
        raise AssertionError("signal: 2D contact-thirds metric is missing")
    third_counts = [int(value) for value in third_counts_value.split(",")]
    if len(third_counts) != 3 or any(value <= 0 for value in third_counts):
        raise AssertionError(
            f"signal: 2D contact-third counts are incomplete: {third_counts}"
        )
    plateau_widths_value = page.locator("#micro-svg").get_attribute(
        "data-plateau-widths"
    )
    if plateau_widths_value is None:
        raise AssertionError("signal: 2D plateau-width metrics are missing")
    plateau_widths = [
        float(value) for value in plateau_widths_value.split(",") if value
    ]
    if not plateau_widths or max(plateau_widths) < 8:
        raise AssertionError(
            f"signal: contact plateau is not visibly widened: {plateau_widths}"
        )
    if page.locator(".micro-contact-segment").count() != len(plateau_widths):
        raise AssertionError("signal: plateau metrics do not match contact segments")
    contact_cap_widths_value = page.locator("#micro-svg").get_attribute(
        "data-contact-cap-widths"
    )
    if contact_cap_widths_value is None:
        raise AssertionError("signal: 2D contact-cap width metrics are missing")
    contact_cap_widths = [
        float(value) for value in contact_cap_widths_value.split(",") if value
    ]
    if len(contact_cap_widths) != len(plateau_widths):
        raise AssertionError(
            "signal: 2D contact-cap metrics do not match contact segments"
        )
    if any(width > 28 for width in contact_cap_widths):
        raise AssertionError(
            f"signal: 2D coupling caps are too wide for peak-top contact: {contact_cap_widths}"
        )
    footprint_widths_value = page.locator("#micro-svg").get_attribute(
        "data-contact-footprint-widths"
    )
    if footprint_widths_value is None:
        raise AssertionError("signal: 2D contact-footprint metrics are missing")
    footprint_widths = [
        float(value) for value in footprint_widths_value.split(",") if value
    ]
    for cap_width, footprint_width in zip(contact_cap_widths, footprint_widths):
        if footprint_width > 0 and cap_width > footprint_width * 0.68:
            raise AssertionError(
                "signal: 2D yellow cap covers too much of the asperity footprint; "
                f"cap={cap_width:.2f}, footprint={footprint_width:.2f}"
            )
    shared_mask_signature = page.locator("#micro-svg").get_attribute(
        "data-contact-mask-signature"
    )
    if not shared_mask_signature:
        raise AssertionError("signal: shared contact-mask signature is missing")
    camera_mask_signature = page.locator(".camera-contact").get_attribute(
        "data-contact-mask-signature"
    )
    if camera_mask_signature != shared_mask_signature:
        raise AssertionError(
            "signal: camera response is not driven by the shared contact mask; "
            f"camera={camera_mask_signature}, microscope={shared_mask_signature}"
        )
    camera_contact_area = page.locator(".camera-contact").get_attribute(
        "data-contact-area"
    )
    if camera_contact_area is None or float(camera_contact_area) <= 0:
        raise AssertionError("signal: camera contact area metric is missing")
    camera_mode = page.locator(".camera-contact").get_attribute(
        "data-response-mode"
    )
    if camera_mode != "dark-disk-annular-dimming":
        raise AssertionError(f"signal: camera response mode is incorrect: {camera_mode}")
    annulus_strength = page.locator(".camera-contact").get_attribute(
        "data-annulus-strength"
    )
    if annulus_strength is None or not 0 < float(annulus_strength) < 1:
        raise AssertionError(
            f"signal: camera annular dimming strength is missing or invalid: {annulus_strength}"
        )
    camera_shape = page.locator(".camera-contact").get_attribute(
        "data-contact-shape"
    )
    if camera_shape is None:
        raise AssertionError("signal: camera contact-shape metric is missing")
    camera_rx, camera_ry = [float(value) for value in camera_shape.split(",")]
    circularity_error = abs(camera_rx - camera_ry) / max(camera_rx, camera_ry)
    if circularity_error > 0.12:
        raise AssertionError(
            f"signal: cylinder-indenter camera response should be circular; "
            f"shape={camera_shape}, circularity_error={circularity_error:.3f}"
        )
    curved_caps = page.locator(".micro-contact-segment[data-cap-curvature]")
    if curved_caps.count() != len(plateau_widths):
        raise AssertionError("signal: 2D contact marks do not expose curved cap metrics")
    cap_curvatures = [
        float(value)
        for value in curved_caps.evaluate_all(
            "elements => elements.map(element => element.dataset.capCurvature || '0')"
        )
    ]
    if any(value <= 0 for value in cap_curvatures):
        raise AssertionError(
            f"signal: 2D contact caps should retain slight curvature: {cap_curvatures}"
        )
    contact_stroke_widths = [
        float(value[:-2]) if value.endswith("px") else float(value)
        for value in curved_caps.evaluate_all(
            "elements => elements.map(element => getComputedStyle(element).strokeWidth)"
        )
    ]
    if any(width > 2.3 for width in contact_stroke_widths):
        raise AssertionError(
            f"signal: 2D coupling highlights are too wide: {contact_stroke_widths}"
        )
    macro_line_width = page.locator("#macro-coupling-line").evaluate(
        "element => getComputedStyle(element).strokeWidth"
    )
    macro_line_width_value = (
        float(macro_line_width[:-2]) if macro_line_width.endswith("px")
        else float(macro_line_width)
    )
    if macro_line_width_value > 2.4:
        raise AssertionError(
            f"signal: macro coupling highlight is too wide: {macro_line_width}"
        )
    macro_mask_signature = page.locator("#macro-coupling-line").get_attribute(
        "data-contact-mask-signature"
    )
    if macro_mask_signature != shared_mask_signature:
        raise AssertionError(
            "signal: macro coupling line is not using the shared contact mask; "
            f"macro={macro_mask_signature}, microscope={shared_mask_signature}"
        )
    macro_chord_width = page.locator("#macro-coupling-line").get_attribute(
        "data-coupling-chord-width"
    )
    macro_deformation_span = page.locator("#macro-coupling-line").get_attribute(
        "data-membrane-deformation-span"
    )
    if macro_chord_width is None or macro_deformation_span is None:
        raise AssertionError("signal: macro coupling geometry metrics are missing")
    macro_chord = float(macro_chord_width)
    deformation_span = float(macro_deformation_span)
    if macro_chord <= 0:
        raise AssertionError("signal: macro coupling chord should be visible at 55%")
    if deformation_span > 0 and macro_chord > deformation_span * 0.42:
        raise AssertionError(
            "signal: macro coupling highlight is too wide relative to membrane "
            f"deformation; chord={macro_chord:.2f}, deformation={deformation_span:.2f}"
        )

    pressure.fill("100")
    high_pressure_cap_widths_value = page.locator("#micro-svg").get_attribute(
        "data-contact-cap-widths"
    )
    if high_pressure_cap_widths_value is None:
        raise AssertionError("signal: high-pressure 2D cap metrics are missing")
    high_pressure_cap_widths = [
        float(value) for value in high_pressure_cap_widths_value.split(",") if value
    ]
    if any(width > 28 for width in high_pressure_cap_widths):
        raise AssertionError(
            "signal: high-pressure microscope coupling caps are too wide: "
            f"{high_pressure_cap_widths}"
        )
    high_pressure_macro_chord = page.locator("#macro-coupling-line").get_attribute(
        "data-coupling-chord-width"
    )
    high_pressure_deformation_span = page.locator("#macro-coupling-line").get_attribute(
        "data-membrane-deformation-span"
    )
    if high_pressure_macro_chord is None or high_pressure_deformation_span is None:
        raise AssertionError("signal: high-pressure macro metrics are missing")
    high_pressure_chord = float(high_pressure_macro_chord)
    high_pressure_deformation = float(high_pressure_deformation_span)
    if high_pressure_chord > 100:
        raise AssertionError(
            f"signal: high-pressure macro contact chord is too wide: {high_pressure_chord:.2f}"
        )
    if high_pressure_deformation > 0 and high_pressure_chord > high_pressure_deformation * 0.42:
        raise AssertionError(
            "signal: high-pressure macro highlight exceeds deformation span; "
            f"chord={high_pressure_chord:.2f}, deformation={high_pressure_deformation:.2f}"
        )

    micro_3d.click()
    if micro_3d.get_attribute("aria-selected") != "true":
        raise AssertionError("signal: 3D microscope tab did not activate")
    if panel_3d.is_hidden() or not panel_2d.is_hidden():
        raise AssertionError("signal: microscope panel did not switch to 3D")

    canvas_box = page.locator("#micro-canvas").bounding_box()
    if canvas_box is None:
        raise AssertionError("signal: #micro-canvas has no rendered bounding box")
    backing_size = page.locator("#micro-canvas").evaluate(
        "canvas => ({ width: canvas.width, height: canvas.height })"
    )
    expected_width = round(canvas_box["width"] * 2)
    expected_height = round(canvas_box["height"] * 2)
    if backing_size != {"width": expected_width, "height": expected_height}:
        raise AssertionError(
            "signal: canvas backing store does not match CSS size at DPR 2; "
            f"expected {expected_width}x{expected_height}, found "
            f"{backing_size['width']}x{backing_size['height']}"
        )

    contact_cells = []
    field_signature = None
    for pressure_value in representative_pressures:
        pressure.fill(str(pressure_value))
        cell_count = page.locator("#micro-canvas").get_attribute(
            "data-contact-cells"
        )
        if cell_count is None:
            raise AssertionError("signal: 3D contact-cell metric is missing")
        contact_cells.append(int(cell_count))
        signature = page.locator("#micro-canvas").get_attribute(
            "data-field-signature"
        )
        if not signature:
            raise AssertionError("signal: 3D field signature is missing")
        if field_signature is None:
            field_signature = signature
        elif signature != field_signature:
            raise AssertionError("signal: 3D field changed across pressure renders")
    if contact_cells != sorted(contact_cells):
        raise AssertionError(
            f"signal: 3D contact cells are not monotonic: {contact_cells}"
        )

    pressure.fill("55")
    quadrant_counts_value = page.locator("#micro-canvas").get_attribute(
        "data-contact-quadrants"
    )
    if quadrant_counts_value is None:
        raise AssertionError("signal: 3D contact-quadrants metric is missing")
    quadrant_counts = [
        int(value) for value in quadrant_counts_value.split(",")
    ]
    if len(quadrant_counts) != 4 or any(
        value <= 0 for value in quadrant_counts
    ):
        raise AssertionError(
            f"signal: 3D contact quadrants are incomplete: {quadrant_counts}"
        )
    canvas_mask_signature = page.locator("#micro-canvas").get_attribute(
        "data-contact-mask-signature"
    )
    if canvas_mask_signature != shared_mask_signature:
        raise AssertionError(
            "signal: 3D microscope is not using the shared contact mask; "
            f"canvas={canvas_mask_signature}, microscope={shared_mask_signature}"
        )
    flattened_cells = page.locator("#micro-canvas").get_attribute(
        "data-flattened-cells"
    )
    if flattened_cells is None or int(flattened_cells) <= 0:
        raise AssertionError("signal: 3D contact islands are not visibly flattened")
    cap_curvature_3d = page.locator("#micro-canvas").get_attribute(
        "data-cap-curvature"
    )
    if cap_curvature_3d is None or float(cap_curvature_3d) <= 0:
        raise AssertionError("signal: 3D contact caps do not retain slight curvature")

    micro_3d.focus()
    page.keyboard.press("ArrowRight")
    if micro_2d.get_attribute("aria-selected") != "true":
        raise AssertionError("signal: ArrowRight from 3D did not wrap to 2D")
    page.keyboard.press("ArrowLeft")
    if micro_3d.get_attribute("aria-selected") != "true":
        raise AssertionError("signal: ArrowLeft from 2D did not wrap to 3D")
    page.keyboard.press("Home")
    if micro_2d.get_attribute("aria-selected") != "true":
        raise AssertionError("signal: Home did not select the 2D tab")
    page.keyboard.press("End")
    if micro_3d.get_attribute("aria-selected") != "true":
        raise AssertionError("signal: End did not select the 3D tab")

    page.reload(wait_until="domcontentloaded")
    if page.locator("#micro-svg").get_attribute(
        "data-profile-signature"
    ) != profile_signature:
        raise AssertionError("signal: 2D profile changed after reload")
    page.locator("#micro-tab-3d").click()
    try:
        page.wait_for_function(
            "() => document.querySelector('#micro-canvas')"
            "?.dataset.fieldSignature !== undefined",
            timeout=4000,
        )
    except PlaywrightTimeoutError as error:
        raise AssertionError(
            "signal: 3D field signature never appeared after reload"
        ) from error
    if page.locator("#micro-canvas").get_attribute(
        "data-field-signature"
    ) != field_signature:
        raise AssertionError("signal: 3D field changed after reload")
    pressure = page.locator("#signal-pressure")

    pressure.fill("80")
    if page.locator("#toolbar-state").inner_text() != "Expanded coupling":
        raise AssertionError("signal: pressure output did not update")
    canvas_summary = page.locator("#micro-canvas").get_attribute("aria-label") or ""
    if "Expanded coupling" not in canvas_summary:
        raise AssertionError("signal: 3D microscope did not receive pressure state")

    play = page.locator("#play-sequence")
    play.click()
    page.wait_for_timeout(2400)
    if play.get_attribute("aria-pressed") != "false":
        raise AssertionError("signal: finite playback did not stop")
    if page.locator("#pressure-percent").inner_text() != "100%":
        raise AssertionError("signal: finite playback did not reach its endpoint")

    play.click()
    page.wait_for_timeout(180)
    pressure.fill("24")
    if play.get_attribute("aria-pressed") != "false":
        raise AssertionError("signal: user input did not cancel playback")
    if issues:
        raise AssertionError(f"signal interactions: {'; '.join(issues)}")
    page.close()
    context.close()


def check_keyboard_focus(browser) -> None:
    for route_name, path in ROUTES.items():
        page = browser.new_page(viewport=VIEWPORTS["desktop"])
        block_media(page)
        navigate(page, path)
        page.keyboard.press("Tab")
        tag = page.evaluate("() => document.activeElement?.tagName")
        if tag not in {"A", "BUTTON", "INPUT"}:
            raise AssertionError(f"{route_name}: first tab stop is not interactive")
        page.close()


def check_reduced_motion(browser) -> None:
    context = browser.new_context(
        viewport=VIEWPORTS["desktop"], reduced_motion="reduce"
    )
    for route_name, path in ROUTES.items():
        page = context.new_page()
        block_media(page)
        issues = collect_runtime_issues(page)
        navigate(page, path)
        reveal_count = page.locator("[data-reveal], [data-preview]").count()
        if reveal_count:
            hidden_count = page.locator(
                "[data-reveal], [data-preview]"
            ).evaluate_all(
                """elements => elements.filter(element => {
                    const style = getComputedStyle(element);
                    return Number(style.opacity) < 0.99 || style.transform !== 'none';
                }).length"""
            )
            if hidden_count:
                raise AssertionError(
                    f"{route_name}: {hidden_count} elements still move or hide "
                    "under reduced motion"
                )
        if issues:
            raise AssertionError(
                f"{route_name} reduced motion: {'; '.join(issues)}"
            )
        page.close()
    context.close()


AUDIT_VIEWPORTS = {
    "phone": {"width": 375, "height": 812},
    "tablet": {"width": 768, "height": 1024},
    "laptop": {"width": 1280, "height": 800},
    "wide": {"width": 1920, "height": 1080},
}

# Distinct rendered font sizes permitted per route. These are ceilings on
# sprawl, not targets: concept-01 once rendered seventeen sizes with 1px
# steps that carried no meaning.
MAX_DISTINCT_FONT_SIZES = {
    "review": 6,
    "optical": 11,
    "atlas": 10,
    "signal": 8,
}

CONTRAST_JS = r"""
(() => {
  const lum = (c) => {
    const f = c.map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  };
  const parse = (s) => {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(parseFloat);
    return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 };
  };
  const bgOf = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0.85) return c.rgb;
      n = n.parentElement;
    }
    const r = parse(getComputedStyle(document.body).backgroundColor);
    return r ? r.rgb : [255, 255, 255];
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };

  const fails = [];
  const sizes = new Set();
  const touch = [];
  document.querySelectorAll('body *').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;

    if (['A', 'BUTTON', 'INPUT', 'SELECT'].includes(el.tagName)
        && r.height > 0 && (r.height < 44 || r.width < 44)) {
      touch.push({
        tag: el.tagName, id: el.id || '',
        w: Math.round(r.width), h: Math.round(r.height),
        text: (el.textContent || '').trim().slice(0, 24)
      });
    }

    const txt = (el.textContent || '').trim();
    if (!txt || el.children.length) return;
    sizes.add(parseFloat(cs.fontSize).toFixed(1));
    const fg = parse(cs.color);
    if (!fg) return;
    const bg = bgOf(el);
    const eff = fg.rgb.map((c, i) => c * fg.a + bg[i] * (1 - fg.a));
    const cr = ratio(eff, bg);
    const px = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    const need = (px >= 24 || (px >= 18.66 && bold)) ? 3.0 : 4.5;
    if (cr < need) {
      fails.push({
        cr: +cr.toFixed(2), need, px: +px.toFixed(1),
        color: cs.color, text: txt.slice(0, 40)
      });
    }
  });
  return {
    fails, touch,
    sizes: [...sizes].map(Number).sort((a, b) => a - b),
    overflow: document.documentElement.scrollWidth
              - document.documentElement.clientWidth
  };
})()
"""


def check_design_system(browser) -> None:
    """Guard the four defect classes found in the 5-round design audit:
    contrast, touch targets, font-size sprawl and horizontal overflow."""
    for route_name, path in ROUTES.items():
        for vp_name, viewport in AUDIT_VIEWPORTS.items():
            page = browser.new_page(viewport=viewport)
            block_media(page)
            navigate(page, path)
            page.wait_for_timeout(250)
            data = page.evaluate(CONTRAST_JS)

            if data["overflow"] > 0:
                raise AssertionError(
                    f"{route_name}@{vp_name}: page scrolls horizontally by "
                    f"{data['overflow']}px"
                )
            if data["fails"]:
                worst = sorted(data["fails"], key=lambda f: f["cr"])[:3]
                raise AssertionError(
                    f"{route_name}@{vp_name}: {len(data['fails'])} text nodes "
                    f"below WCAG AA contrast; worst: {worst}"
                )
            if vp_name in {"phone", "tablet"} and data["touch"]:
                raise AssertionError(
                    f"{route_name}@{vp_name}: touch targets under 44px: "
                    f"{data['touch'][:4]}"
                )
            limit = MAX_DISTINCT_FONT_SIZES[route_name]
            if len(data["sizes"]) > limit:
                raise AssertionError(
                    f"{route_name}@{vp_name}: {len(data['sizes'])} distinct "
                    f"font sizes exceeds {limit}: {data['sizes']}"
                )
            page.close()


def check_media_scaling(browser) -> None:
    """The mechanism animation must stay proportioned and crisp everywhere."""
    for vp_name, viewport in AUDIT_VIEWPORTS.items():
        page = browser.new_page(viewport=viewport, device_scale_factor=2)
        navigate(page, ROUTES["signal"])
        page.wait_for_timeout(300)

        box = page.locator("#micro-svg").bounding_box()
        aspect = box["width"] / box["height"]
        if abs(aspect - 520 / 320) > 0.08:
            raise AssertionError(
                f"signal@{vp_name}: microscope section is letterboxed or "
                f"stretched; aspect {aspect:.2f} vs 1.63"
            )

        page.locator("#micro-tab-3d").click()
        page.wait_for_timeout(400)
        canvas = page.evaluate(
            """() => {
              const c = document.querySelector('#micro-canvas');
              const r = c.getBoundingClientRect();
              return { backing: c.width, css: r.width, dpr: window.devicePixelRatio };
            }"""
        )
        scale = canvas["backing"] / max(canvas["css"], 1)
        if scale < canvas["dpr"] - 0.05:
            raise AssertionError(
                f"signal@{vp_name}: 3D canvas renders below device pixel "
                f"ratio ({scale:.2f} vs {canvas['dpr']}) and will look soft"
            )
        page.close()


def check_coupling_readability(browser) -> None:
    """The two views that state a coupled percentage must look like it.

    Both drifted from their own readouts: the 3D field rendered 90.9% amber
    while reporting 98.5%, because the membrane grid was drawn over the gold
    sheet; and the camera disc covered half the frame at 99% coupled, because
    a pixel size clamped at 180px could not fill a panel of any other size.
    """
    page = browser.new_page(viewport={"width": 1440, "height": 1000},
                            device_scale_factor=2)
    navigate(page, ROUTES["signal"])

    page.locator("#micro-tab-3d").click()
    page.wait_for_timeout(400)
    page.locator("#signal-pressure").fill("100")
    page.wait_for_timeout(450)

    amber = page.evaluate(
        """() => {
          // Measure the mesh region only: the top band holds the panel's
          // white caption text, which is not part of the rendered field and
          // dilutes the statistic.
          const c = document.querySelector('#micro-canvas');
          const W = c.width, H = c.height;
          const d = c.getContext('2d').getImageData(0, 0, W, H).data;
          let mesh = 0, weighted = 0;
          for (let y = Math.floor(H * 0.24); y < H; y += 1) {
            for (let x = 0; x < W; x += 1) {
              const i = (y * W + x) * 4;
              if (d[i + 3] < 200) continue;
              const r = d[i], g = d[i + 1], b = d[i + 2];
              if (r + g + b < 90) continue;
              mesh += 1;
              weighted += Math.max(0, Math.min(1, (r - b) / 150));
            }
          }
          return weighted / Math.max(mesh, 1);
        }"""
    )
    model = page.evaluate("contactRatio(couplingPressureFor(1))")
    if amber < model - 0.03:
        raise AssertionError(
            f"signal: 3D field draws {amber:.1%} amber but reports "
            f"{model:.1%} coupled; the picture contradicts the readout"
        )

    geo = page.evaluate(
        """() => {
          const s = document.querySelector('.camera-stage').getBoundingClientRect();
          const b = document.querySelector('.camera-contact').getBoundingClientRect();
          return { cover: Math.min(b.width / s.width, 1),
                   dx: b.x + b.width / 2 - (s.x + s.width / 2),
                   dy: b.y + b.height / 2 - (s.y + s.height / 2) };
        }"""
    )
    if abs(geo["dx"]) > 1 or abs(geo["dy"]) > 1:
        raise AssertionError(
            f"signal: camera response is off-centre by "
            f"({geo['dx']:.1f}, {geo['dy']:.1f})px"
        )
    if geo["cover"] < 0.95:
        raise AssertionError(
            f"signal: camera response spans only {geo['cover']:.0%} of the "
            f"sensor frame at full compression"
        )
    page.close()


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        if MODE in {"all", "visual"}:
            for viewport_name, viewport in VIEWPORTS.items():
                for route_name, path in ROUTES.items():
                    check_route(
                        browser, route_name, path, viewport_name, viewport
                    )
        if MODE in {"all", "behavior"}:
            check_optical_interactions(browser)
            check_atlas_interactions(browser)
            check_signal_interactions(browser)
            check_keyboard_focus(browser)
            check_reduced_motion(browser)
        if MODE in {"all", "design"}:
            check_design_system(browser)
            check_media_scaling(browser)
            check_coupling_readability(browser)
        browser.close()
    if MODE in {"all", "visual"}:
        print(f"PASS: 4 routes × 2 viewports; screenshots: {OUTPUT}")
    if MODE in {"all", "behavior"}:
        print("PASS: interactions, keyboard focus, reduced motion, console, network")
    if MODE in {"all", "design"}:
        print(
            "PASS: contrast, touch targets, type scale, overflow, "
            "media scaling, coupling readability"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
