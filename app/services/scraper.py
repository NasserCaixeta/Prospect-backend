import re
from dataclasses import asdict, dataclass
from urllib.parse import quote_plus

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


def extract_brazilian_phone(text: str) -> str | None:
    patterns = (
        r"\+55\s?\d{2}\s?\d{4,5}-?\d{4}",
        r"\(\d{2}\)\s?\d{4,5}-\d{4}",
        r"\b\d{2}\s\d{4,5}-\d{4}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return None


def is_probable_whatsapp_phone(normalized_phone: str | None) -> bool:
    if not normalized_phone:
        return False
    digits = re.sub(r"\D+", "", normalized_phone)
    if digits.startswith("55") and len(digits) == 13:
        digits = digits[2:]
    return len(digits) == 11 and digits[2] == "9"


class GoogleMapsScraper:
    blocked_markers = ("captcha", "unusual traffic", "não sou um robô", "nao sou um robo")

    def search(self, *, city: str, state: str, segment: str, max_results: int) -> list[dict]:
        query = f"{segment} em {city} {state}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(
                    f"https://www.google.com/maps/search/{quote_plus(query)}",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                page.wait_for_timeout(5000)
                if self._is_blocked(page.content()):
                    raise ScraperBlockedError("Google Maps blocked automated access")
                results: list[dict] = []
                cards = page.locator('[role="article"]').all()[:max_results]
                for card in cards:
                    if len(results) >= max_results:
                        break
                    page.wait_for_timeout(700)
                    text = card.inner_text(timeout=3000)
                    name = text.splitlines()[0].strip() if text.strip() else None
                    link_locator = card.locator("a.hfpxzc").first
                    if link_locator.count() == 0:
                        link_locator = card.locator('a[href*="/maps/place"]').first
                    link = link_locator.get_attribute("href", timeout=3000)
                    if name and link:
                        lines = [line.strip() for line in text.splitlines() if line.strip()]
                        rating = self._extract_rating(lines)
                        category, address = self._extract_category_and_address(lines)
                        phone = self._read_detail_phone(page, link)
                        results.append(
                            ScrapedLead(
                                name=name,
                                google_maps_url=link,
                                phone=phone,
                                category=category,
                                address=address,
                                rating=rating,
                            ).to_dict()
                        )
                return results
            except PlaywrightTimeoutError as exc:
                raise RuntimeError("Google Maps search timed out") from exc
            finally:
                browser.close()

    def _is_blocked(self, html: str) -> bool:
        lowered = html.lower()
        return any(marker in lowered for marker in self.blocked_markers)

    def _extract_rating(self, lines: list[str]) -> float | None:
        for line in lines[1:4]:
            if re.fullmatch(r"\d+[,.]\d+", line):
                return float(line.replace(",", "."))
        return None

    def _extract_category_and_address(self, lines: list[str]) -> tuple[str | None, str | None]:
        for line in lines:
            if "·" in line:
                parts = [part.strip(" \ue934") for part in line.split("·")]
                parts = [part for part in parts if part]
                category = parts[0] if parts else None
                address = parts[-1] if len(parts) > 1 else None
                return category, address
        return None, None

    def _extract_detail_phone(self, detail_text: str) -> str | None:
        return extract_brazilian_phone(detail_text)

    def _read_detail_phone(self, page, link: str) -> str | None:
        try:
            page.goto(link, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2500)
            if self._is_blocked(page.content()):
                raise ScraperBlockedError("Google Maps requested manual verification")
            return self._extract_detail_phone(page.locator("body").inner_text(timeout=5000))
        except ScraperBlockedError:
            raise
        except Exception:
            return None
