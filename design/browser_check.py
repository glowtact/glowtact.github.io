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
    if page.locator("#camera-canvas").count() != 1:
        raise AssertionError("signal: camera response is not rendered from the model")
    camera_stage_box = page.locator(".camera-stage").bounding_box()
    if camera_stage_box is None:
        raise AssertionError("signal: camera stage has no rendered box")
    camera_aspect = camera_stage_box["width"] / camera_stage_box["height"]
    if abs(camera_aspect - (4 / 3)) > 0.08:
        raise AssertionError(
            f"signal: camera ROI aspect ratio {camera_aspect:.3f} is not close to 4:3"
        )
    # The frame must be synthesised, never a supplied tactile image scaled up.
    camera_uses_bitmap = page.locator(".camera-stage").evaluate(
        "element => [...element.querySelectorAll('*')].some(node =>"
        " node.tagName === 'IMG' ||"
        " getComputedStyle(node).backgroundImage.includes('.png') ||"
        " getComputedStyle(node).backgroundImage.includes('.jpg'))"
    )
    if camera_uses_bitmap:
        raise AssertionError("signal: camera response embeds a supplied tactile bitmap")
    default_opacity = float(
        page.locator(".camera-contact").evaluate(
            "element => getComputedStyle(element).opacity"
        )
    )
    if default_opacity > 0.05:
        raise AssertionError(
            f"signal: camera contact should be hidden at 0%, opacity {default_opacity}"
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
    coupled_fractions: list[tuple[int, float]] = []
    camera_levels: list[tuple[int, float]] = []
    profile_signature = None
    for pressure_value in dense_pressures:
        pressure.fill(str(pressure_value))
        assert_centered(page, ".camera-contact", ".camera-stage")
        minimum_clearance = page.locator("#micro-svg").get_attribute(
            "data-minimum-clearance"
        )
        if minimum_clearance is None:
            raise AssertionError("signal: 2D minimum-clearance metric is missing")
        # The membrane may rest on a flattened asperity, so zero clearance is
        # the expected coupled state. What must never happen is penetration.
        if float(minimum_clearance) < -1e-3:
            raise AssertionError(
                f"signal: membrane penetrates the gel ({minimum_clearance}) "
                f"at {pressure_value}% pressure"
            )
        coupled_fraction_value = page.locator("#micro-svg").get_attribute(
            "data-coupled-fraction"
        )
        if coupled_fraction_value is None:
            raise AssertionError("signal: 2D coupled-fraction metric is missing")
        coupled_fraction = float(coupled_fraction_value)
        if coupled_fraction <= 0:
            # Unloaded or pre-contact: an open air gap must still be visible.
            if float(minimum_clearance) <= 2.0:
                raise AssertionError(
                    f"signal: no visible air gap ({minimum_clearance}) while "
                    f"uncoupled at {pressure_value}% pressure"
                )
        elif float(minimum_clearance) > 0.5:
            raise AssertionError(
                f"signal: contact is not conformal; clearance "
                f"{minimum_clearance} at {pressure_value}% pressure"
            )
        coupled_fractions.append((pressure_value, coupled_fraction))
        centre_level = page.evaluate(
            """() => {
              const canvas = document.querySelector('#camera-canvas');
              const context = canvas.getContext('2d');
              const size = 24;
              const data = context.getImageData(
                (canvas.width - size) / 2, (canvas.height - size) / 2, size, size
              ).data;
              let total = 0;
              for (let i = 0; i < data.length; i += 4) total += data[i + 1];
              return total / (data.length / 4);
            }"""
        )
        camera_levels.append((pressure_value, round(centre_level, 2)))
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
    fractions = [value for _, value in coupled_fractions]
    if fractions != sorted(fractions):
        raise AssertionError(
            f"signal: coupled fraction is not monotonic: {coupled_fractions}"
        )
    if fractions[-1] <= 0.2:
        raise AssertionError(
            f"signal: coupled fraction stays negligible at full load: {fractions[-1]}"
        )
    # The rendered frame must keep darkening across the whole slider range.
    levels = [value for _, value in camera_levels]
    if levels != sorted(levels, reverse=True):
        raise AssertionError(
            f"signal: camera frame is not monotonically darkening: {camera_levels}"
        )
    if levels[0] - levels[-1] < 60:
        raise AssertionError(
            f"signal: camera frame barely responds across the range: {camera_levels}"
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
        browser.close()
    if MODE in {"all", "visual"}:
        print(f"PASS: 4 routes × 2 viewports; screenshots: {OUTPUT}")
    if MODE in {"all", "behavior"}:
        print("PASS: interactions, keyboard focus, reduced motion, console, network")
    return 0


if __name__ == "__main__":
    sys.exit(main())
