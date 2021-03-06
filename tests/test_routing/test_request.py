import pytest

from ellar.common import Cookie, Header
from ellar.core import TestClientFactory
from ellar.core.routing import ModuleRouter

mr = ModuleRouter("")


@mr.get("/headers1")
def headers1(request, user_agent: str = Header(...)):
    return user_agent


@mr.get("/headers2")
def headers2(request, ua: str = Header(..., alias="User-Agent")):
    return ua


@mr.get("/headers3")
def headers3(request, content_length: int = Header(...)):
    return content_length


@mr.get("/headers4")
def headers4(request, c_len: int = Header(..., alias="Content-length")):
    return c_len


@mr.get("/headers5")
def headers5(request, missing: int = Header(...)):
    return missing


@mr.get("/cookies1")
def cookies1(request, weapon: str = Cookie(...)):
    return weapon


@mr.get("/cookies2")
def cookies2(request, wpn: str = Cookie(..., alias="weapon")):
    return wpn


tm = TestClientFactory.create_test_module(routers=(mr,))
client = tm.get_client()


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/headers1", 200, "Ellar"),
        ("/headers2", 200, "Ellar"),
        ("/headers3", 200, 10),
        ("/headers4", 200, 10),
        (
            "/headers5",
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "missing"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        ("/cookies1", 200, "shuriken"),
        ("/cookies2", 200, "shuriken"),
    ],
)
def test_headers(path, expected_status, expected_response):
    response = client.get(
        path,
        headers={"User-Agent": "Ellar", "Content-Length": "10"},
        cookies={"weapon": "shuriken"},
    )
    assert response.status_code == expected_status, response.content
    assert response.json() == expected_response
