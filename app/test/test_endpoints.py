import io
import zipfile

from fastapi.testclient import TestClient
import pytest

# pytest handles this path resolution correctly even though it is highlighted as
# incorrect in an IDE
from main.main import app, ANDROID_USER, ANDROID_PASSWORD, STRUCTURE_JSON_FILENAME


def get_token() -> str:
    return test_successful_login()


def test_successful_login() -> str:
    with TestClient(app) as client:
        response = client.post("/authenticate", data={"username": ANDROID_USER, "password": ANDROID_PASSWORD})
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
    with TestClient(app) as client:
        response = client.post("/authenticate", data=wrong_data)
        assert response.status_code == 400  # Bad Request


@pytest.mark.parametrize("data", [{"username": ANDROID_USER},
                                  {"password": ANDROID_PASSWORD},
                                  ])
def test_invalid_login_request(data: dict[str, str]) -> None:
    with TestClient(app) as client:
        response = client.post("/authenticate", data=data)
        assert response.status_code == 422  # Unprocessable Entity


def test_get_languages() -> list[dict[str, str, str]]:
    with TestClient(app) as client:
        response = client.get("/languages", headers={"Authorization": f"Bearer {get_token()}"})
        assert response.status_code == 200  # OK
        response_data = response.json()
        for lang in response_data:
            assert "code" in lang
            assert "name" in lang
        assert isinstance(response_data, list)
        assert len(response_data) > 0
        return response_data


def test_files() -> None:
    with TestClient(app) as client:
        for lang_code in test_get_languages():
            response = client.get(f"/files/{lang_code['code']}", headers={"Authorization": f"Bearer {get_token()}"})
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"
            assert response.headers["content-disposition"] == f"attachment; filename=\"files_{lang_code['code']}.zip\""
            assert response.headers["content-length"] == str(len(response.content))

            with zipfile.ZipFile(io.BytesIO(response.content), "r") as f:
                assert STRUCTURE_JSON_FILENAME in f.namelist()
