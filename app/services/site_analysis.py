import re
from dataclasses import dataclass, field
from time import perf_counter

import httpx

from app.models.enums import SiteAnalysisStatus


@dataclass(frozen=True)
class WebsiteAnalysisResult:
    status: SiteAnalysisStatus
    score: int
    issues: list[str] = field(default_factory=list)
    analysis_data: dict[str, object] = field(default_factory=dict)


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def analyze_website(url: str | None) -> WebsiteAnalysisResult:
    if not url:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SEM_SITE,
            score=0,
            issues=["missing_website_url"],
        )

    issues: list[str] = []
    if not url.lower().startswith("https://"):
        issues.append("missing_https")

    started_at = perf_counter()
    try:
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
    except httpx.TimeoutException:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_RUIM,
            score=20,
            issues=[*issues, "timeout"],
            analysis_data={"url": url},
        )
    except httpx.HTTPError as exc:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_RUIM,
            score=20,
            issues=[*issues, "request_error"],
            analysis_data={"url": url, "error": str(exc)},
        )

    elapsed_ms = int((perf_counter() - started_at) * 1000)
    if response.status_code >= 400:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_RUIM,
            score=25,
            issues=[*issues, "http_error"],
            analysis_data={"url": url, "status_code": response.status_code},
        )

    if elapsed_ms > 5000:
        issues.append("slow_response")

    title = _extract_title(response.text)
    if not title or title.lower() in {"home", "inicio", "início", "index"}:
        issues.append("generic_or_missing_title")

    score = max(0, 100 - (20 * len(issues)))
    status = SiteAnalysisStatus.SITE_RUIM if score < 50 else SiteAnalysisStatus.SITE_OK
    return WebsiteAnalysisResult(
        status=status,
        score=score,
        issues=issues,
        analysis_data={
            "url": url,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "title": title,
        },
    )
