#  Copyright (c) 2023 Jonas Bischofberger. All rights reserved.

import io
import json
import os
import zipfile

import requests
import yaml
import pprint

tmp_dir = "extract_test"


def test_languages():
    response = requests.get("http://127.0.0.1:8000/languages")
    if response.status_code == 200:
        languages = json.loads(response.content)
        print(f"{languages=}")
    else:
        print(f'Error: {response.status_code}: {json.loads(response.content)["detail"]}')


def test_files_unsuccessful():
    response = requests.get("http://127.0.0.1:8000/files/sv")
    if response.status_code == 200:
        files = json.loads(response.content)
        print(f"{files=}")
    else:
        print(f'Error: {response.status_code}: {json.loads(response.content)["detail"]}')


def test_files_successful():
    response = requests.get("http://127.0.0.1:8000/files/de")
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content), "r") as f:
            f.extractall(path=tmp_dir)

        # Iterate over extracted files in regular directory
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                print("Extracted file:", os.path.join(root, file))

        clear_tmp_folder()
    else:
        print(f'Error: {response.status_code}: {response.content=}')


def clear_tmp_folder():
    for root, dirs, files in os.walk(tmp_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(tmp_dir)


def test_all():
    languages = json.loads(requests.get("http://127.0.0.1:8000/languages").content)
    print(f"{languages=}")
    for selected_language in languages["lang_codes"]:
    # for selected_language in ["en"]:
        with zipfile.ZipFile(io.BytesIO(requests.get(f"http://127.0.0.1:8000/files/{selected_language}").content), "r") as f:
            f.extractall(path=tmp_dir)
            with open(os.path.join(tmp_dir, "structure.yaml"), "r", encoding="utf-8") as f:
                structure = yaml.safe_load(f)

        structure_by_file = {}

        for root, _, files in os.walk(tmp_dir, topdown=False):
            for name in files:
                if name == "structure.yaml":
                    continue
                file_path = os.path.join(root, name)
                rel_file_on_disk = os.path.relpath(file_path, tmp_dir)

                found_file_in_yaml = False
                found_languages_in_yaml = []

                for category in structure["categories"]:
                    for unit in category["units"]:
                        for file in unit["files"]:
                            if os.path.normpath(file) == os.path.normpath(rel_file_on_disk):
                                structure_by_file.setdefault(file_path, {}).setdefault("category", []).append(category["name"])
                                structure_by_file.setdefault(file_path, {}).setdefault("unit", []).append(unit["name"])

        print(f"{selected_language=}")
        print(f"{structure_by_file=}")
        pprint.pprint(structure)



def main():
    # test_languages()
    # test_files_unsuccessful()
    # test_files_successful()
    test_all()

if __name__ == '__main__':
    main()