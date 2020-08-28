import json
from pathlib import Path
import sys
import logging

# Add some colors to the logging output
logging.addLevelName(logging.DEBUG, "\x1b[38;21m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
logging.addLevelName(logging.INFO, "\x1b[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\x1b[33;21m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\x1b[31;21m%s\033[1;0m" % logging.getLevelName(logging.ERROR))


# Paths
class _Paths:
    def __init__(self):
        self.ROOT = Path(__file__).parent.parent
        self._output = None

    @property
    def OUTPUT(self):
        return self._output if self._output else self.ROOT / "dist"

    @OUTPUT.setter
    def OUTPUT(self, value):
        self._output = Path(value)

    @property
    def DATA(self):
        return self.ROOT / "data"

    @property
    def ASSETS(self):
        return self.ROOT / "assets"

    @property
    def MOVES_OUTPUT(self):
        return self.OUTPUT / "moves"

    @property
    def POKEMON_OUTPUT(self):
        return self.OUTPUT / "pokemon"


# Instantiate our Path class
Paths = _Paths()


# Constants
ATTRIBUTES = ["STR", "CON", "DEX", "INT", "WIS", "CHA"]


def __load(path):
    with path.open(encoding="utf-8") as fp:
        json_data = json.load(fp)
    return json_data


def load_extra(name):
    p = Path(Paths.ASSETS / "extra" / name).with_suffix(".json")
    return __load(p)


# Data holders that's read in to memory for simplicity
MERGE_POKEMON_DATA = load_extra("pokemon")
MERGE_EVOLVE_DATA = load_extra("evolve")
MERGE_FILTER_DATA = load_extra("filter_data")
MERGE_MOVE_DATA = load_extra("moves")
MERGE_ABILITY_DATA = load_extra("abilities")
VARIANT_DATA = load_extra("variants")

options = {"remove_dice": False, "output": False}


def update_options(_options):
    merge(options, _options)
    Paths.OUTPUT = _options["output"] if _options["output"] else Paths.OUTPUT


def merge(a, b, path=None):
    """merges b into a"""
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same value
            else:  # Overwrite value
                a[key] = b[key]
                # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def diff_dict(base, other):
    diff = {}
    for k,v in other.items():
        if not k in base:
            diff[k] = v
        else:
            if type(v) is dict:
                inner_diff = diff_dict(base[k], v)
                if bool(inner_diff):
                    diff[k] = inner_diff
            else:
                if base[k] != v:
                    diff[k] = v
    return diff

def update_progress(progress):
    bar_length = 50  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length*progress))
    text = "\rPercent: [{}] {:.1f}% {}".format("#"*block + "-"*(bar_length-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()


def ensure_int(value):
    if value:
        return int(value)
    return None


def ensure_float(value):
    if value:
        return float(value)
    return None


def ensure_string(value):
    if value and value != "None":
        return value.strip('"').strip()
    return None


def ensure_list(value, sep=','):
    if value:
        return [ensure_string(x) for x in value.split(sep)]
    return None


def clean_object(obj):
    if not obj:
        return
    for index in range(len(obj))[::-1]:
        if not obj[index] or obj[index] == "None":
            del obj[index]


def clean_dict(d):
    if type(d) is dict:
        return dict((k, clean_dict(v)) for k, v in d.items() if v is not None)
        # return {k: v for k, clean_output(v) in d.items() if v is not None}
    else:
        return d
