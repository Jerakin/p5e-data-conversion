# How to get all that data?

# Setup
## Install dependencies
`pip install -r requirements.txt`

# Download data
## `gspread`
* **Setup gspread** https://gspread.readthedocs.io/en/latest/oauth2.html
  * Don't forget to download your token
* Share the document with your gserviceaccount

## Download individual sheets
Go to your copy of the `DM Pokémon Builder Gen I - VI.xlsx` document. Download all sheets called `*DATA`, naming them e.g. `PDATA.csv`

## Convert
Convert to the format the app wants with `python main.py <path to token OR folder with Downloaded sheets> --output <path to where json should be output>`
