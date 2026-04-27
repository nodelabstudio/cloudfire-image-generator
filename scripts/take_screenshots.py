"""Capture marketing screenshots of the running Cloudfire app.

Prereq: server running at BASE_URL with a populated test user (designtest /
testpass123 created earlier in this session, with several gallery images and
one shared via /api/image/<id>/share).

Output: docs/screenshots/*.png
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8765"
USERNAME = "designtest"
PASSWORD = "testpass123"
SHARE_TOKEN = "64d34581dfed7bf3e2363b78836f3771"

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 1440, "height": 900}


PUBLIC = [
    ("01-login.png",            "/login"),
    ("02-register.png",         "/register"),
    ("03-forgot-password.png",  "/forgot-password"),
    ("04-share.png",            f"/s/{SHARE_TOKEN}"),
]

PRIVATE = [
    ("05-studio.png",     "/"),
    ("06-gallery.png",    "/gallery"),
    ("07-dashboard.png",  "/dashboard"),
]


async def shoot(page, filename: str, full_page: bool = True):
    target = OUT / filename
    await page.wait_for_load_state("networkidle")
    # Give animations / fonts a beat to settle
    await page.wait_for_timeout(900)
    await page.screenshot(path=str(target), full_page=full_page)
    print(f"  -> {target.relative_to(OUT.parent.parent)}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # Public pages: fresh context, no cookies
        ctx = await browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = await ctx.new_page()
        for name, path in PUBLIC:
            print(f"public {path}")
            await page.goto(BASE_URL + path)
            await shoot(page, name)
        await ctx.close()

        # Private pages: log in via UI, then screenshot
        ctx = await browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(BASE_URL + "/login")
        await page.fill("#username", USERNAME)
        await page.fill("#password", PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_url(BASE_URL + "/")
        for name, path in PRIVATE:
            print(f"private {path}")
            await page.goto(BASE_URL + path)
            await shoot(page, name)
        await ctx.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
