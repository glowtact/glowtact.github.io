"""Capture focused review screenshots of the Concept 3 mechanism section."""

from pathlib import Path
import os
import sys

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("GLOWTACT_BASE_URL", "http://127.0.0.1:4173")
OUT = Path(os.environ.get("GLOWTACT_SHOT_OUTPUT", "/tmp/glowtact-shots"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, device_scale_factor=2
        )
        page = context.new_page()
        page.route(
            "**/*.{mp4,webm,mov}", lambda route: route.fulfill(status=204, body="")
        )
        page.emulate_media(reduced_motion="reduce")
        page.goto(f"{BASE_URL}/concept-03/", wait_until="networkidle")

        page.locator(".signal-hero").screenshot(path=str(OUT / "hero.png"))

        section = page.locator("#mechanism")
        section.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        pressure = page.locator("#signal-pressure")

        for value in ("0", "35", "55", "100"):
            pressure.fill(value)
            page.wait_for_timeout(160)
            section.screenshot(path=str(OUT / f"mech-2d-{value}.png"))

        page.locator("#micro-tab-3d").click()
        page.wait_for_timeout(320)
        for value in ("0", "55", "100"):
            pressure.fill(value)
            page.wait_for_timeout(160)
            section.screenshot(path=str(OUT / f"mech-3d-{value}.png"))

        page.locator(".macro-stage").screenshot(path=str(OUT / "macro-stage.png"))

        mobile = browser.new_context(
            viewport={"width": 390, "height": 844}, device_scale_factor=2
        )
        mobile_page = mobile.new_page()
        mobile_page.route(
            "**/*.{mp4,webm,mov}", lambda route: route.fulfill(status=204, body="")
        )
        mobile_page.emulate_media(reduced_motion="reduce")
        mobile_page.goto(f"{BASE_URL}/concept-03/", wait_until="networkidle")
        mobile_page.locator("#mechanism").scroll_into_view_if_needed()
        mobile_page.wait_for_timeout(400)
        mobile_page.locator("#signal-pressure").fill("55")
        mobile_page.wait_for_timeout(200)
        mobile_page.locator("#mechanism").screenshot(
            path=str(OUT / "mech-mobile.png")
        )

        browser.close()
    print(f"screenshots: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
