import json

import pytest

from dev_assistant.corpus import Passage
from dev_assistant.model import MISSING, validated_answer

PART = Passage("inventory.sql", 8, 9, "CHECK (reserved <= on_hand)")


def test_answer_returns_exact_source_and_quote():
    result = validated_answer(
        '{"source":1,"quote":"reserved <= on_hand","answer":"SQL enforces it."}', [PART]
    )
    assert result.source == PART
    assert result.quote in PART.body


@pytest.mark.parametrize(
    ("source", "quote"), [(0, "CHECK"), (2, "CHECK"), (True, "CHECK"), (1, "invented"), (1, " ")]
)
def test_unknown_id_or_unsupported_quote_abstains(source, quote):
    result = validated_answer(json.dumps(dict(source=source, quote=quote, answer="guess")), [PART])
    assert result.text == MISSING and result.source is None


def test_malformed_model_response_is_an_error():
    with pytest.raises(ValueError):
        validated_answer("not JSON", [PART])
