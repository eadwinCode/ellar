import json

import pytest

from ellar.constants import SCOPE_SERVICE_PROVIDER
from ellar.core.connection import HTTPConnection, Request, WebSocket
from ellar.core.context import IExecutionContext
from ellar.core.middleware import RequestServiceProviderMiddleware
from ellar.core.response import Response
from ellar.di import EllarInjector

from ..injector_module import Configuration, DummyModule


async def assert_service_provider_app(scope, receive, send):
    assert scope[SCOPE_SERVICE_PROVIDER]

    service_provider = scope[SCOPE_SERVICE_PROVIDER]
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    _config_repr = repr(service_provider.get(Configuration))
    str_provider = service_provider.get(str)
    await send(
        dict(
            type="http.response.body",
            body=json.dumps(
                {"str": str_provider, "configuration": _config_repr}
            ).encode(),
        )
    )


async def assert_iexecute_context_app(scope, receive, send):
    assert scope[SCOPE_SERVICE_PROVIDER]

    service_provider = scope[SCOPE_SERVICE_PROVIDER]
    execution_context: IExecutionContext = service_provider.get(IExecutionContext)
    assert (
        service_provider.get(HTTPConnection)
        is execution_context.switch_to_http_connection()
    )
    assert service_provider.get(Request) is execution_context.switch_to_request()
    assert service_provider.get(Response) is execution_context.get_response()
    assert service_provider is execution_context.get_service_provider()

    with pytest.raises(Exception):
        execution_context.switch_to_websocket()

    with pytest.raises(Exception):
        service_provider.get(WebSocket)

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send(
        dict(
            type="http.response.body",
            body=json.dumps({"message": "execution context work"}).encode(),
        )
    )


def test_di_middleware(test_client_factory):
    injector_ = EllarInjector()
    injector_.container.install(DummyModule)
    asgi_app = RequestServiceProviderMiddleware(
        assert_service_provider_app, debug=False, injector=injector_
    )

    client = test_client_factory(asgi_app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["str"] == "Ellar"
    assert data["configuration"] == repr(injector_.get(Configuration))


def test_di_middleware_execution_context_initialization(test_client_factory):
    asgi_app = RequestServiceProviderMiddleware(
        assert_iexecute_context_app, debug=False, injector=EllarInjector()
    )

    client = test_client_factory(asgi_app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "execution context work"
