import io
import zipfile

import fastapi.testclient
import pytest

from files import app, ANDROID_USER, ANDROID_PASSWORD, STRUCTURE_JSON_FILENAME

test_client = fastapi.testclient.TestClient(app)


def get_token() -> str:
    return test_successful_login()


def test_successful_login() -> str:
    response = test_client.post("/authenticate", data={"username": ANDROID_USER, "password": ANDROID_PASSWORD})
    assert response.status_code == 200  # OK
    response_data = response.json()
    assert "access_token" in response_data
    assert isinstance(response_data["access_token"], str)
    return response_data["access_token"]


@pytest.mark.parametrize("wrong_data", [{"username": ANDROID_USER, "password": "incorrect_password"},
                                        {"username": "incorrect_user", "password": ANDROID_PASSWORD},
                                        {"username": "incorrect_user", "password": "incorrect_password"},
                                        ])
def test_unsuccessful_login(wrong_data: dict[str, str]) -> None:
    response = test_client.post("/authenticate", data=wrong_data)
    assert response.status_code == 400  # Bad Request


@pytest.mark.parametrize("data", [{"username": ANDROID_USER},
                                  {"password": ANDROID_PASSWORD},
                                  ])
def test_invalid_login_request(data: dict[str, str]) -> None:
    response = test_client.post("/authenticate", data=data)
    assert response.status_code == 422  # Unprocessable Entity


def test_get_languages() -> dict[str, list[str]]:
    response = test_client.get("/languages", headers={"Authorization": f"Bearer {get_token()}"})
    assert response.status_code == 200  # OK
    response_data = response.json()
    assert "lang_codes" in response_data
    assert "lang_names" in response_data
    assert isinstance(response_data["lang_codes"], list)
    assert isinstance(response_data["lang_names"], list)
    assert len(response_data["lang_codes"]) == len(response_data["lang_names"])
    assert len(response_data["lang_codes"]) > 0
    return response_data


def test_files() -> None:
    for lang_code in test_get_languages()["lang_codes"]:
        response = test_client.get(f"/files/{lang_code}", headers={"Authorization": f"Bearer {get_token()}"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert response.headers["content-disposition"] == f"attachment; filename=\"files_{lang_code}.zip\""
        assert response.headers["content-length"] == str(len(response.content))

        with zipfile.ZipFile(io.BytesIO(response.content), "r") as f:
            assert STRUCTURE_JSON_FILENAME in f.namelist()
