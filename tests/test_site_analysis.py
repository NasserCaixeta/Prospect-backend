import httpx

from app.models.enums import SiteAnalysisStatus


def test_analyze_missing_url_marks_no_site():
    from app.services.site_analysis import analyze_website

    result = analyze_website(None)

    assert result.status == SiteAnalysisStatus.SEM_SITE
    assert result.issues == ["missing_website_url"]


def test_analyze_timeout_marks_bad_site(monkeypatch):
    from app.services import site_analysis

    def fake_get(*args, **kwargs):
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr(site_analysis.httpx, "get", fake_get)

    result = site_analysis.analyze_website("https://example.com")

    assert result.status == SiteAnalysisStatus.SITE_RUIM
    assert "timeout" in result.issues


def test_analyze_http_error_marks_bad_site(monkeypatch):
    from app.services import site_analysis

    def fake_get(*args, **kwargs):
        return httpx.Response(500, text="error", request=httpx.Request("GET", "https://x.test"))

    monkeypatch.setattr(site_analysis.httpx, "get", fake_get)

    result = site_analysis.analyze_website("https://x.test")

    assert result.status == SiteAnalysisStatus.SITE_RUIM
    assert "http_error" in result.issues


def test_analyze_non_https_records_issue(monkeypatch):
    from app.services import site_analysis

    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            text="<html><head><title>Empresa Local</title></head></html>",
            request=httpx.Request("GET", "http://x.test"),
        )

    monkeypatch.setattr(site_analysis.httpx, "get", fake_get)

    result = site_analysis.analyze_website("http://x.test")

    assert result.status == SiteAnalysisStatus.SITE_OK
    assert "missing_https" in result.issues


def test_analyze_good_https_site_is_ok(monkeypatch):
    from app.services import site_analysis

    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            text="<html><head><title>Empresa Local</title></head></html>",
            request=httpx.Request("GET", "https://x.test"),
        )

    monkeypatch.setattr(site_analysis.httpx, "get", fake_get)

    result = site_analysis.analyze_website("https://x.test")

    assert result.status == SiteAnalysisStatus.SITE_OK
    assert result.score == 100
