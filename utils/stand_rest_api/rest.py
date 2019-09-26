# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module defines server that receives files and saves them at local directory.

Server receives files at `/upload/<dir_name>` endpoint and saves them at <dir_name> directory. If <dir_name> is already
exists, before saving files server deletes the entire contents of the directory.

To save files at <dir_name> directory with `curl` run:

curl -X POST "http://<host>:<port>/upload/<dir_name>" -H  "accept: application/json" -H  "t-Type: multipart/form-data" \
    -F "files=@file_a.py" -F "files=@file_b.txt"

To save files at <dir_name> directory with `requests` module run in interpreter:

import requests
requests.post("http://<host>:<port>/upload/<dir_name>", files=[('files', open('file_a.py', 'rb')),
                                                               ('files', open('file_b.txt', 'rb'))])

"""
from pathlib import Path
from shutil import rmtree
from typing import List

import uvicorn
from fastapi import FastAPI, File, UploadFile

app = FastAPI()
root_path = Path('/path/to/root/directory/').resolve()
chunk_size = 1024


@app.post("/upload/{dir_name}")
async def create_folder(dir_name: str, files: List[UploadFile] = File(...)) -> dict:
    folder_path = root_path / dir_name
    if folder_path.is_file():
        folder_path.unlink()
    elif folder_path.is_dir():
        rmtree(folder_path, ignore_errors=True)
    folder_path.mkdir(parents=True)

    for uploaded_file in files:
        file_path = folder_path / uploaded_file.filename
        with open(file_path, 'wb') as local_file:
            chunk = await uploaded_file.read(chunk_size)
            while chunk:
                local_file.write(chunk)
                chunk = await uploaded_file.read(chunk_size)

    return {'status': f'{len(files)} have uploaded'}


if __name__ == '__main__':
    uvicorn.run(app)
