import httpx
import pytest

from dev_assistant.model import Ollama


def mock_model(handler):
    model = Ollama()
    model.close()
    model.client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    return model


def test_embeddings_batch_and_preserve_order():
    import json

    sizes = []

    def respond(request):
        inputs = json.loads(request.content)["input"]
        sizes.append(len(inputs))
        return httpx.Response(200, json={"embeddings": [[1, int(s)] for s in inputs]})

    model = mock_model(respond)
    try:
        assert model.embed([str(i) for i in range(20)]) == [[1, i] for i in range(20)]
        assert sizes == [16, 4]
    finally:
        model.close()


@pytest.mark.parametrize("vectors", [[], [[0, 0]], [[]]])
def test_embedding_protocol_rejects_invalid_batch(vectors):
    model = mock_model(lambda _: httpx.Response(200, json={"embeddings": vectors}))
    try:
        with pytest.raises(ValueError, match="embeddings"):
            model.embed(["question"])
    finally:
        model.close()


def test_offline_ollama_is_an_operational_error():
    def offline(_):
        raise httpx.ConnectError("offline")

    model = mock_model(offline)
    try:
        with pytest.raises(httpx.ConnectError):
            model.embed(["question"])
        assert model.answer("no hits", []).source is None
    finally:
        model.close()
