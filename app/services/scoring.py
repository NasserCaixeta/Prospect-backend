from app.models.enums import DigitalPresence, PotentialLevel

PRIORITY_SEGMENTS = {
    "barbearia",
    "barbearias",
    "salao de beleza",
    "salão de beleza",
    "oficina mecanica",
    "oficina mecânica",
    "restaurante",
    "clinica estetica",
    "clínica estética",
}


def classify_potential(score: int) -> PotentialLevel:
    if score >= 80:
        return PotentialLevel.ALTO
    if score >= 50:
        return PotentialLevel.MEDIO
    return PotentialLevel.BAIXO


def calculate_score(
    *,
    phone: str | None,
    digital_presence: DigitalPresence,
    segment: str | None,
    review_count: int | None,
    has_incomplete_data: bool,
) -> tuple[int, PotentialLevel]:
    score = 0
    if phone:
        score += 25
    if digital_presence == DigitalPresence.SEM_SITE:
        score += 40
    if digital_presence == DigitalPresence.SITE_RUIM:
        score += 30
    if segment and segment.strip().lower() in PRIORITY_SEGMENTS:
        score += 15
    if review_count is not None and review_count >= 50:
        score += 10
    if has_incomplete_data:
        score -= 10
    score = max(0, min(100, score))
    return score, classify_potential(score)
