import copy
import hashlib
import datetime
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

PORT = 443

app = fastapi.FastAPI()

file_root = os.path.join(os.path.dirname(__file__), "files")
structure_yaml_path = os.path.join(file_root, "structure.yaml")
global_structure = dict
supported_langs = []
oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl="authenticate")


def generate_access_token() -> str:
    now = datetime.datetime.utcnow()
    data = {"sub": ANDROID_USER, "exp": now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME_MINUTES),
            "iat": now}
    encoded_jwt = jose.jwt.encode(data, PRIVATE_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/authenticate")
async def authenticate(form_data: fastapi.security.OAuth2PasswordRequestForm = fastapi.Depends()):
    if form_data.username != ANDROID_USER or form_data.password != ANDROID_PASSWORD:
        raise fastapi.HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": generate_access_token(), "token_type": "bearer"}


@app.get("/languages")
async def get_languages(token: str = fastapi.Depends(oauth2_scheme)):
    return supported_langs


@app.get("/files/{lang_code}")
async def get_files_by_langcode(lang_code: str, token: str = fastapi.Depends(oauth2_scheme)):
    if lang_code not in get_supported_lang_codes(global_structure):
        raise fastapi.HTTPException(status_code=404, detail=f"Language {lang_code} ({langname_by_langcode(lang_code)}) "
                                                            f"not supported. Supported languages: {', '.join([f'{lang_code} ({langname_by_langcode(lang_code)})' for lang_code in get_supported_lang_codes(global_structure)])}")
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


def get_language_specific_structure(lang_code: str, structure_internal: dict):
    structure = copy.deepcopy(structure_internal)
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


def get_supported_lang_codes(structure_internal: dict) -> list[str]:
    return list(get_file_list_by_langcode(structure_internal).keys())


def langname_by_langcode(langcode: str) -> str:
    return langcodes.Language.get(langcode).display_name(language=langcode)


def get_file_list_by_langcode(structure_internal: dict) -> dict[str, list[str]]:
    lang2files: dict[str, list[str]] = {}
    for category in structure_internal["categories"]:
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
        for filename in get_file_list_by_langcode(global_structure)[lang_code]:
            f.write(filename, arcname=os.path.relpath(filename, start=file_root))

        # Add structure as yaml file to zip without writing the yaml file to disk first
        lang_specific_structure = get_language_specific_structure(lang_code, global_structure)
        f.writestr("structure.yaml", yaml.dump(lang_specific_structure, allow_unicode=True))

    return zip_filename


def generate_supported_langcodes(structure_internal: dict) -> []:
    supported_langcodes = get_supported_lang_codes(structure_internal)
    result = []
    for langcode in supported_langcodes:
        lang_structure_md5 = hashlib.md5(
            yaml.dump(get_language_specific_structure(langcode, structure_internal), allow_unicode=True).encode(
                'utf-8')).hexdigest()
        langname_by_langcode(langcode)
        result.append({"code": langcode, "name": langname_by_langcode(langcode), "md5": lang_structure_md5})
    return result


def main():
    # todo default port to run outside of docker
    #     uvicorn.run(app, port=PORT)
    uvicorn.run(app)


if __name__ == '__main__':
    global_structure = read_file_structure_yaml()
    supported_langs = generate_supported_langcodes(global_structure)

    main()
