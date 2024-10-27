import os
import pandas as pd
import uvicorn
import shutil
import uuid

from io import BytesIO
from pathlib import Path
from typing import Annotated
from loguru import logger

from litestar import Litestar, get, post
from litestar.exceptions import NotAuthorizedException, ValidationException
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import File, Template
from litestar.contrib.htmx.response import ClientRedirect
from litestar.background_tasks import BackgroundTask

from funcs import DocWriter

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "http://0.0.0.0:8000")
OUT_PATH = Path(__file__).parent / "out"

OUT_PATH.mkdir(exist_ok=True)


# All files created are temporary, so remove them once download to client is complete
async def cleanup(id: uuid) -> None:
    logger.info(f"Cleanup: {id}")
    # Remove zip file
    for f in OUT_PATH.iterdir():
        if f.name == f"{id}.zip":
            f.unlink()

    # Remove folder contents
    dir_target: Path = OUT_PATH / id
    for f in dir_target.iterdir():
        f.unlink()
    # Remove empty folder
    dir_target.rmdir()
    logger.info(f"Clean up complete: {id}")


@post(path="/up")
async def handle_file_upload(
    data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> ClientRedirect | str:
    """
    Post end point called with excel file
    Create directory with unique id
    Read excel file
    Template docx files (/doc_templates/) populated with details from Excel file, save new files in new directory (/out/{ID})
    Zip that directory + redirect client to download
    """

    content = await data.read()
    if not data.filename.endswith("xls") and not data.filename.endswith("xlsx"):
        logger.info(f"Unsupported file type - {data.filename}")
        return "File type not valid, select another file."

    df = pd.read_excel(BytesIO(content))
    logger.info(data.filename)

    # create "temporary" unique folder
    id = uuid.uuid4().hex
    curr_folders = {folder.name for folder in OUT_PATH.iterdir() if folder.is_dir()}
    while id in curr_folders:
        id = uuid.uuid4().hex
    out_folder = OUT_PATH / id
    out_folder.mkdir()

    # generate docs, store in unique out_folder
    doc_writing = DocWriter(df, out_folder).generate_docs()
    if not doc_writing:
        cleanup(id)
        return

    # make zip file, store in level above the out_folder to avoid zip trying to zip itself
    # filename (can include path), file type, folder to zip
    shutil.make_archive(f"{OUT_PATH / id}", "zip", out_folder)

    return ClientRedirect(f"/down?id={id}")


@get(path="/down")
async def handle_file_download(id: str | None) -> File:
    """
    Download zip file with given id
    background_task deletes zip + directory
    """
    # TODO: id = None for testing only, remove later
    if not id:
        df = pd.read_excel("test_data/ABC_Ltd.xlsx")

        # create unique folder
        id = uuid.uuid4().hex
        curr_folders = {folder.name for folder in OUT_PATH.iterdir() if folder.is_dir()}
        while id in curr_folders:
            id = uuid.uuid4().hex
        out_folder = OUT_PATH / id
        out_folder.mkdir()

        DocWriter(df, out_folder).generate_docs()

        # make zip file: filename (can include path), file type, folder to zip
        shutil.make_archive(f"{OUT_PATH / id}", "zip", out_folder)

        file_path = OUT_PATH / f"{id}.zip"
        return File(
            path=file_path, filename="out.zip", background=BackgroundTask(cleanup, id)
        )

    file_path = OUT_PATH / f"{id}.zip"
    logger.info(file_path)
    return File(
        path=file_path, filename="out.zip", background=BackgroundTask(cleanup, id)
    )


@get(path="/")
async def hello() -> Template:
    return Template(template_name="index.html")


app = Litestar(
    route_handlers=[
        hello,
        handle_file_upload,
        handle_file_download,
        create_static_files_router(path="/static", directories=["src/assets"]),
    ],
    template_config=TemplateConfig(
        directory=Path("src/templates"),
        engine=JinjaTemplateEngine,
    ),
    debug=True,
)

if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload_delay=5,
        reload=BACKEND_SERVER_URL == "http://0.0.0.0:8000",
    )
