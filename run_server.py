import copy
import datetime
import json
import os.path
import zipfile

import fastapi
import langcodes
import uvicorn
import yaml
import fastapi.security

import jose.jwt

ANDROID_USER = "android"
ANDROID_PASSWORD = "password"

STRUCTURE_JSON_FILENAME = "structure.json"

PRIVATE_KEY = "5ff8ed89479c9ca882214142f274c0bc764627cba15328f8240d122ea24b9527"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_TIME_MINUTES = 30

app = fastapi.FastAPI()

file_root = os.path.join(os.path.dirname(__file__), "files")
structure_yaml_path = os.path.join(file_root, "structure.yaml")

oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl="authenticate")


def generate_access_token() -> str:
    now = datetime.datetime.utcnow()
    data = {"sub": ANDROID_USER, "exp": now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME_MINUTES), "iat": now}
    encoded_jwt = jose.jwt.encode(data, PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/authenticate")
async def authenticate(form_data: fastapi.security.OAuth2PasswordRequestForm = fastapi.Depends()):
    if form_data.username != ANDROID_USER or form_data.password != ANDROID_PASSWORD:
        raise fastapi.HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": generate_access_token(), "token_type": "bearer"}


@app.get("/languages")
async def get_languages(token: str = fastapi.Depends(oauth2_scheme)):
    lang_codes = get_supported_lang_codes()
    return {"lang_codes": lang_codes, "lang_names": [langname_by_langcode(lang_code) for lang_code in lang_codes]}


@app.get("/files/{lang_code}")
async def get_files_by_langcode(lang_code: str, token: str = fastapi.Depends(oauth2_scheme)):
    if lang_code not in get_supported_lang_codes():
        raise fastapi.HTTPException(status_code=404, detail=f"Language {lang_code} ({langname_by_langcode(lang_code)}) "
                                                            f"not supported. Supported languages: {', '.join([f'{lang_code} ({langname_by_langcode(lang_code)})' for lang_code in get_supported_lang_codes()])}")
    zip_filename = get_zip(lang_code)
    return fastapi.responses.FileResponse(path=zip_filename, filename=zip_filename, media_type="application/zip")
    # with open(zip_filename, "rb") as f:
    #     return fastapi.responses.StreamingResponse(io.BytesIO(f.read()), media_type="application/zip")


def read_file_structure_yaml():
    with open(structure_yaml_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise exc


def get_language_specific_structure(lang_code: str):
    structure = read_file_structure_yaml()
    new_structure = copy.deepcopy(structure)
    for category in reversed(structure["categories"]):
        if lang_code in category["name"]:
            category["name"] = category["name"][lang_code]
            for unit in reversed(category.get("units", [])):
                if lang_code in unit["name"]:
                    unit["name"] = unit["name"][lang_code]
                    if lang_code in unit["files"]:
                        unit["files"] = unit["files"][lang_code]
                    else:
                        unit["files"] = []
                else:
                    category["units"].remove(unit)
            for question in reversed(category.get("questions", [])):
                if lang_code in question["question"]:
                    question["question"] = question["question"][lang_code]
                    for answer in reversed(question["answers"]):
                        if lang_code in answer["answer"]:
                            answer["answer"] = answer["answer"][lang_code]
                        else:
                            question["answers"].remove(answer)
                else:
                    category["questions"].remove(question)
        else:
            del structure["categories"][structure["categories"].index(category)]

    return structure


def get_supported_lang_codes() -> list[str]:
    return list(get_file_list_by_langcode().keys())


def langname_by_langcode(langcode: str) -> str:
    return langcodes.Language.get(langcode).display_name(language=langcode)


def get_file_list_by_langcode() -> dict[str, list[str]]:
    structure = read_file_structure_yaml()
    lang2files: dict[str, list[str]] = {}
    for category in structure["categories"]:
        for lang in category["name"]:
            lang2files.setdefault(lang, [])
        for unit in category["units"]:
            for lang in unit["files"]:
                lang_std = langcodes.standardize_tag(lang)
                for file in unit["files"][lang]:
                    lang2files.setdefault(lang_std, []).append(os.path.join(file_root, file))

    return lang2files


def get_zip(lang_code: str) -> str:
    zip_filename = f"files_{lang_code}.zip"
    with zipfile.ZipFile(zip_filename, "w") as f:
        for filename in get_file_list_by_langcode()[lang_code]:
            f.write(filename, arcname=os.path.relpath(filename, start=file_root))

        # Add structure as JSON (not yaml) file to zip without writing it to disk
        structure = get_language_specific_structure(lang_code)
        f.writestr(STRUCTURE_JSON_FILENAME, json.dumps(structure, ensure_ascii=False))

    return zip_filename


def main():
    uvicorn.run(app)


if __name__ == '__main__':
    main()
