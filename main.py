from pathlib import Path
import sys
import logging
import argparse

from gspread.exceptions import SpreadsheetNotFound

try:
    import scripts.source_data.converters.other as other
    import scripts.source_data.converters.moves as moves
    import scripts.source_data.converters.pokemon as pokemon
    import scripts.source_data.util.fetch_data as fetch
    import scripts.source_data.util.util as util
except ModuleNotFoundError:
    import converters.other as other
    import converters.moves as moves
    import converters.pokemon as pokemon
    import util.fetch_data as fetch
    import util.util as util

data_sheets = {
    "IDATA.csv": other.convert_idata,    # Items
    "MDATA.csv": moves.convert_mdata,    # Moves
    "PDATA.csv": pokemon.convert_pdata,  # Pokemon
    "TDATA.csv": other.convert_tdata     # Abilities
}


def convert_all(folder):
    folder = Path(folder)
    if not folder.exists():
        logging.error(f"Could not find data folder, aborting")
        sys.exit(1)
    if not util.Paths.OUTPUT.exists():
        util.Paths.OUTPUT.mkdir()
        util.Paths.MOVES_OUTPUT.mkdir()
        util.Paths.POKEMON_OUTPUT.mkdir()

    for file_path in folder.iterdir():
        if file_path.name in data_sheets:
            logging.debug(f"Starting converting {file_path.stem}")
            data_sheets[file_path.name](file_path)
            logging.debug(f"Finished converting {file_path.stem}")


def _cli_options():
    parser = argparse.ArgumentParser()
    optional = parser._action_groups.pop()
    optional.add_argument('-k', '--keep-dice', action='store_true', dest="keep_dice")
    optional.add_argument('-o', '--output', dest="output", help="Custom output directory")
    optional.add_argument('-nv', '--no-variants', dest="no_variants", action='store_true', help="Custom output directory")

    required = parser.add_argument_group("required arguments")
    required.add_argument('token', nargs="?",
                          help="File containing gspread token (or path to folder with downloaded Data)")

    parser._action_groups.append(optional)

    return parser


def _run_cli():
    parser = _cli_options()
    options = parser.parse_args()
    util.update_options({
        "remove_dice": not options.keep_dice,
        "output": options.output if options.output else False,
        "variants": not options.no_variants
    })

    if not options.token:
        if (Path(__file__).parent / "data").exists:
            convert_all(Path(__file__).parent / "data")
        else:
            logging.warning("Please provide either a access file or a folder with the Download DATA sheets in")
    else:
        argument = Path(options.token)
        if argument.exists():
            if argument.is_file() and argument.suffix == ".json":
                try:
                    _folder = fetch.main(cred_file=argument)
                except SpreadsheetNotFound:
                    logging.error("SpreadsheetNotFound: Could not find the spreadsheet on the service account")
                    sys.exit(1)
                convert_all(_folder)

            elif argument.is_dir():
                convert_all(argument)
            else:
                logging.error("Access file or folder not found, please provide a valid path")

    logging.info("Conversion finished")


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Conversion started")
    try:
        _run_cli()
    except KeyboardInterrupt:
        logging.warning("Conversion aborted")
        sys.exit()
    except:
        raise


if __name__ == '__main__':
    main()
