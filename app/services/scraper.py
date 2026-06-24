import re
from dataclasses import asdict, dataclass

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class ScraperBlockedError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScrapedLead:
    name: str
    google_maps_url: str
    phone: str | None = None
    address: str | None = None
    category: str | None = None
    website_url: str | None = None
    rating: float | None = None
    review_count: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _extract(pattern: str, html: str) -> str | None:
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def parse_result_card(html: str) -> ScrapedLead:
    maps_url = _extract(r'class="maps-url"[^>]+href="([^"]+)"', html)
    name = _extract(r'class="name"[^>]*>(.*?)</', html)
    if not maps_url or not name:
        raise ValueError("Result card requires name and Google Maps URL")
    rating_text = _extract(r'class="rating"[^>]*>(.*?)</', html)
    reviews_text = _extract(r'class="reviews"[^>]*>(.*?)</', html)
    review_count = None
    if reviews_text:
        digits = re.sub(r"\D+", "", reviews_text)
        review_count = int(digits) if digits else None
    return ScrapedLead(
        name=name,
        google_maps_url=maps_url,
        phone=_extract(r'class="phone"[^>]*>(.*?)</', html),
        address=_extract(r'class="address"[^>]*>(.*?)</', html),
        category=_extract(r'class="category"[^>]*>(.*?)</', html),
        website_url=_extract(r'class="website"[^>]+href="([^"]+)"', html),
        rating=float(rating_text.replace(",", ".")) if rating_text else None,
        review_count=review_count,
    )


class GoogleMapsScraper:
    blocked_markers = ("captcha", "unusual traffic", "não sou um robô", "nao sou um robo")

    def search(self, *, city: str, state: str, segment: str, max_results: int) -> list[dict]:
        query = f"{segment} em {city} {state}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1000)
                if self._is_blocked(page.content()):
                    raise ScraperBlockedError("Google Maps blocked automated access")
                page.get_by_role("combobox").fill(query)
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)
                if self._is_blocked(page.content()):
                    raise ScraperBlockedError("Google Maps requested manual verification")
                # The live DOM is intentionally handled conservatively. Parser coverage stays fixture-based.
                results: list[dict] = []
                cards = page.locator('[role="article"]').all()[:max_results]
                for card in cards:
                    if len(results) >= max_results:
                        break
                    page.wait_for_timeout(700)
                    text = card.inner_text(timeout=3000)
                    name = text.splitlines()[0].strip() if text.strip() else None
                    link = card.locator("a").first.get_attribute("href", timeout=3000)
                    if name and link:
                        results.append(ScrapedLead(name=name, google_maps_url=link).to_dict())
                return results
            except PlaywrightTimeoutError as exc:
                raise RuntimeError("Google Maps search timed out") from exc
            finally:
                browser.close()

    def _is_blocked(self, html: str) -> bool:
        lowered = html.lower()
        return any(marker in lowered for marker in self.blocked_markers)
