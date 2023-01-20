import copy
import os.path
import zipfile

import fastapi
import langcodes
import uvicorn
import yaml

app = fastapi.FastAPI()

file_root = os.path.join(os.path.dirname(__file__), "files")
structure_yaml_path = os.path.join(file_root, "structure.yaml")


@app.get("/languages")
async def get_languages():
    lang_codes = get_supported_lang_codes()
    return {"lang_codes": lang_codes, "lang_names": [langname_by_langcode(lang_code) for lang_code in lang_codes]}

@app.get("/files/{lang_code}")
async def get_files_by_langcode(lang_code: str):
    if lang_code not in get_supported_lang_codes():
        raise fastapi.HTTPException(status_code=404, detail=f"Language {lang_code} ({langname_by_langcode(lang_code)}) "
                f"not supported. Supported languages: {', '.join([f'{lang_code} ({langname_by_langcode(lang_code)})'for lang_code in get_supported_lang_codes()])}")
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

        # Add structure as yaml file to zip without writing the yaml file to disk first
        structure = get_language_specific_structure(lang_code)
        print("lss", yaml.dump(structure, allow_unicode=True))
        f.writestr("structure.yaml", yaml.dump(structure, allow_unicode=True))

    return zip_filename


def main():
    uvicorn.run(app)


if __name__ == '__main__':
    get_language_specific_structure("en")
    main()