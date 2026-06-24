from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_leads: int
    leads_without_site: int
    bad_site_leads: int
    leads_with_phone: int
    contacted_leads: int
    interested_leads: int
    closed_leads: int


class DashboardBreakdown(BaseModel):
    by_city: dict[str, int]
    by_segment: dict[str, int]
    by_status: dict[str, int]
