# -*- coding: utf-8 -*-
import csv
import json
import os
import sys
from pathlib import Path
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

try:
    import scripts.source_data.util.util as util
except ModuleNotFoundError:
    from util import util


DATA_SHEETS = ["IDATA", "MDATA", "PDATA", "TDATA"]


def save_worksheet(worksheet):
    if not util.Paths.DATA.exists():
        util.Paths.DATA.mkdir(parents=True)

    output_file = Path(util.Paths.DATA) / (worksheet.title + ".csv")

    with open(output_file, "w", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"')
        content = worksheet.get_all_values()
        for row in content:
            new_row = []
            for record in row:
                new_row.append(record)
            try:
                writer.writerow(new_row)
            except (UnicodeEncodeError, UnicodeDecodeError):
                print("Caught unicode error")


def get_worksheet(file_or_secret):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    if Path(file_or_secret).is_file():
        with open(file_or_secret, "r") as f:
            cred_data = json.load(f)
    else:
        cred_data = json.loads(file_or_secret)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(cred_data, scope)
    gc = gspread.authorize(credentials)

    return gc.open(r"DM Pokémon Builder Gen I - VII.xlsx")


def main(file_or_secret):
    logging.info("Starting downloading spreadsheets")
    wks = get_worksheet(file_or_secret)
    for worksheet in wks.worksheets():
        if worksheet.title in DATA_SHEETS:
            save_worksheet(worksheet)
    logging.info("Finished downloading spreadsheets")
    return util.Paths.DATA


if __name__ == '__main__':
    if len(sys.argv) == 2:
        credentials_file = sys.argv[1]
        if os.path.exists(credentials_file):
            main(file_or_secret=credentials_file)
        else:
            print("Error: Access file not found, please provide a valid path")
    else:
        print("Please provide the access file")
