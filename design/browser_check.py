from pathlib import Path
import base64
import os
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


def check_signal_interactions(browser) -> None:
    page = browser.new_page(viewport=VIEWPORTS["desktop"])
    block_media(page)
    issues = collect_runtime_issues(page)
    navigate(page, "/concept-03/")
    pressure = page.locator("#signal-pressure")
    pressure.fill("80")
    if page.locator("#toolbar-state").inner_text() != "Expanded coupling":
        raise AssertionError("signal: pressure output did not update")

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
