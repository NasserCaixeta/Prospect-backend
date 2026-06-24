from app.models.enums import DigitalPresence, PotentialLevel


def test_no_site_phone_and_priority_segment_is_high_potential():
    from app.services.scoring import calculate_score

    score, level = calculate_score(
        phone="(19) 99999-9999",
        digital_presence=DigitalPresence.SEM_SITE,
        segment="barbearia",
        review_count=60,
        has_incomplete_data=False,
    )

    assert score == 90
    assert level == PotentialLevel.ALTO


def test_bad_site_contributes_to_score():
    from app.services.scoring import calculate_score

    score, level = calculate_score(
        phone=None,
        digital_presence=DigitalPresence.SITE_RUIM,
        segment=None,
        review_count=None,
        has_incomplete_data=False,
    )

    assert score == 30
    assert level == PotentialLevel.BAIXO


def test_incomplete_data_subtracts_and_score_clamps_to_100():
    from app.services.scoring import calculate_score

    score, level = calculate_score(
        phone="11999999999",
        digital_presence=DigitalPresence.SEM_SITE,
        segment="restaurante",
        review_count=100,
        has_incomplete_data=False,
    )

    assert score == 90
    assert level == PotentialLevel.ALTO

    score, level = calculate_score(
        phone=None,
        digital_presence=DigitalPresence.SITE_DESCONHECIDO,
        segment=None,
        review_count=None,
        has_incomplete_data=True,
    )

    assert score == 0
    assert level == PotentialLevel.BAIXO
