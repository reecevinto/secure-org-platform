from app.core.session_security import generate_session_identifier


def test_session_identifier_is_generated() -> None:
    session_identifier = generate_session_identifier()

    assert isinstance(session_identifier, str)
    assert session_identifier


def test_session_identifiers_are_unique() -> None:
    first_identifier = generate_session_identifier()
    second_identifier = generate_session_identifier()

    assert first_identifier != second_identifier


def test_session_identifier_has_expected_entropy_representation() -> None:
    session_identifier = generate_session_identifier()

    assert len(session_identifier) >= 40
