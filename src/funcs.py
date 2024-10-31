import requests
import pandas as pd
import shutil
import uuid
from docx import Document
from python_docx_replace import docx_replace
from pathlib import Path
from loguru import logger

from dataclasses import dataclass

TEMPLATE_PATH = Path(__file__).parent / "doc_templates"
OUT_PATH = Path(__file__).parent / "out"

TEMPLATE_PATH.mkdir(exist_ok=True)
OUT_PATH.mkdir(exist_ok=True)

# the attribute names are used to make replacements in .docx files using docx_replace
# docx files contain e.g. ${ref} or ${claim_number} (syntax required by docx_replace)
@dataclass
class CompanyInfo:
    ref: str
    app_type: str
    file_created_date: str
    claim_number: str
    claim_issue_date: str
    hearing_date: str
    company_name: str
    company_number: str
    registered_office_address: str
    registered_office_address_postcode: str

    strike_off_method: str
    incorporation_date: str
    last_annual_return_confirmation_date: str
    strike_off_date: str

    claimant_name: str
    claimant_address_multi: str
    claimant_address_one: str
    claimant_address_postcode: str

    member_shareholding: str
    shares_issued: str
    issued_capital: str
    individual_share_value: str

    forename: str
    surname: str
    firm: str
    address: str
    address_postcode: str
    email: str
    telephone: str

def make_post():
    url = 'http://localhost:8000/up'
    with open('test_data/ABC_Ltd.xlsx', 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
        print(response.text)

def zipstuff(out_file, in_dir):
    shutil.make_archive(out_file, "zip", in_dir)

class DocWriter:
    def __init__(self, df: pd.DataFrame, dir: Path):
        # Directory to put files
        self.dir = dir

        # Hardcoded row numbers. Row number in excel sheet - 2 = iloc number
        # Check df is correct length
        if df.shape[0] < 51:
            logger.warning("DF contains less than 51 rows")
            return
        # Put all addresses into list of length 4 for consistency (4 lines is max address length)
        registered_office_address = [x for x in df.iloc[13:17,1].to_list() if not pd.isna(x)]
        registered_office_address = [x for x in registered_office_address if x.strip()]
        registered_office_address = ", ".join(registered_office_address)
        # while len(registered_office_address) < 4:
        #     registered_office_address.append("")

        claimant_address = [x for x in df.iloc[30:34,1].to_list() if not pd.isna(x)]
        claimant_address = [x for x in claimant_address if x.strip()]
        claimant_address_multi = "\n".join(claimant_address)
        claimant_address_one = ", ".join(claimant_address)
        # print(claimant_address_multi)
        # while len(claimant_address) < 4:
        #     claimant_address.append("")

        address = [x for x in df.iloc[44:48,1].to_list() if not pd.isna(x)]
        address = [x for x in address if x.strip()]
        while len(address) < 4:
            address.append("")

        self.client_info = CompanyInfo(
            ref=df.iloc[0,1],
            app_type=df.iloc[2,1],
            file_created_date=df.iloc[5,1],
            claim_number=df.iloc[7,1],
            claim_issue_date=df.iloc[8,1],
            hearing_date=df.iloc[9,1],
            company_name=df.iloc[11,1],
            company_number=df.iloc[12,1],
            registered_office_address=registered_office_address,
            registered_office_address_postcode=df.iloc[17,1],
            strike_off_method=df.iloc[19,1],
            incorporation_date=df.iloc[23,1],
            last_annual_return_confirmation_date=df.iloc[25,1],
            strike_off_date=df.iloc[27,1],
            claimant_name=df.iloc[29,1],
            claimant_address_multi=claimant_address_multi,
            claimant_address_one=claimant_address_one,
            claimant_address_postcode=df.iloc[34,1],
            member_shareholding=df.iloc[36,1],
            shares_issued=df.iloc[37,1],
            issued_capital=df.iloc[38,1],
            individual_share_value=df.iloc[39,1],
            forename=df.iloc[41,1],
            surname=df.iloc[42,1],
            firm=df.iloc[43,1],
            address=address,
            address_postcode=df.iloc[48,1],
            email=df.iloc[49,1],
            telephone=df.iloc[50,1]
        )

    # Populate target dir with the template docs with replacements.
    def generate_docs(self):
        #TODO:
        # Remove highlight from template docs if needed (by editing the docs themselves, not code)

        # loop over template docs
        for f in TEMPLATE_PATH.iterdir():
            if f.name.endswith(".docx"):
                doc = Document(TEMPLATE_PATH / f.name)
                # make replacements, function takes in document, and the "replacement dictionary"
                docx_replace(doc, **self.client_info.__dict__)
                # save doc in target folder
                doc.save(self.dir / f.name)
            #TODO:
            # add PDF replacements here
        return True


def create_unique_folder() -> Path:
    id = uuid.uuid4().hex
    curr_folders = {folder.name for folder in OUT_PATH.iterdir() if folder.is_dir()}
    while id in curr_folders:
        id = uuid.uuid4().hex
    out_folder = OUT_PATH / id
    out_folder.mkdir()
    logger.info(f"Created {out_folder.name}")
    return id, out_folder

def cleanup(id: uuid):
    for f in OUT_PATH.iterdir():
        if f.name == f"{id}.zip":
            f.unlink()
    dir_target: Path = OUT_PATH / id
    for f in dir_target.iterdir():
        f.unlink()
    dir_target.rmdir()



if __name__ == "__main__":
    # make_post()
    # zipstuff()
    df = pd.read_excel(Path(__file__).parent / "test_data" / "ABC_Ltd.xlsx")
    id, out_dir = create_unique_folder()
    DocWriter(df=df, dir=out_dir).generate_docs()
    zipstuff(f"{OUT_PATH / id}", out_dir)
    # create_unique_folder()
    # test = Path(__file__).parent / "out" / "0f554aaedd944fdcbcb562089a0a01f5"
    # cleanup("23f896ace2424d2da8deedba1051929d")
