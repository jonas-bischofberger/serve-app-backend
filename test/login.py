import fastapi.testclient
import pytest

from run_server import app, ANDROID_USER, ANDROID_PASSWORD

test_client = fastapi.testclient.TestClient(app)


def test_successful_login():
    response = test_client.post("/authenticate", data={"username": ANDROID_USER, "password": ANDROID_PASSWORD})
    assert response.status_code == 200  # OK
    response_data = response.json()
    assert "access_token" in response_data
    assert isinstance("access_token", str)


@pytest.mark.parametrize("wrong_data", [{"username": ANDROID_USER, "password": "incorrect_password"},
                                        {"username": "incorrect_user", "password": ANDROID_PASSWORD},
                                        {"username": "incorrect_user", "password": "incorrect_password"},
                                        ])
def test_unsuccessful_login(wrong_data: dict[str, str]):
    response = test_client.post("/authenticate", data=wrong_data)
    assert response.status_code == 400  # Bad Request


@pytest.mark.parametrize("data", [{"username": ANDROID_USER},
                                  {"password": ANDROID_PASSWORD},
                                  ])
def test_invalid_login_request(data: dict[str, str]):
    response = test_client.post("/authenticate", data=data)
    assert response.status_code == 422  # Unprocessable Entity
