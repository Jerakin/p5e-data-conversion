import re
import csv
import json
import logging

try:
    import scripts.source_data.util.util as util
except ModuleNotFoundError:
    from util import util

POKEMON = "Pokémon"
DEFAULT_HEADER = ("Index Number", "Evo Stages with Eviolite", "Evo Stages w/o Eviolite", POKEMON, "Type", "SR", "AC",
                  "Hit Dice", "HP", "", "", "WSp", "Ssp", "Fsp", "Senses", "STR", "DEX", "CON", "INT", "WIS", "CHA",
                  "MIN LVL FD", "Ev", "Evolve", "Evo Stages", "ST1", "ST2", "ST3", "Skill", "Res", "Vul", "Imm",
                  "Ability1", "Ability2", "HiddenAbility", "Moves", "Evolution for sheet", "Evolve Bonus",
                  "Climbing Speed", "Burrowing Speed", "Description 17", "Size")


def clean_file_name(value):
    return value.replace(" ♀", "-f").replace(" ♂", "-m").replace("é", "e").replace("\n", " ").replace(":", "")


def fix_species_name(value):
    return value.replace("\n", " ")


class Pokemon:
    RE_STARTING_MOVES = re.compile("Starting Moves: ([A-Za-z ,-12'’]*)")
    RE_TM_MOVES = re.compile("TM: (.*)")
    RE_EGG_MOVES = re.compile("Egg Moves: (.*)")
    RE_LEVEL_MOVES = re.compile("Level (\d+): ([A-Za-z ,'-’]*)")

    def __init__(self, header):
        self.header = header
        self.name = None
        self.output_data = {}
        self.valid = True

    def setup_basic_stats(self, csv_row):
        self.output_data["index"] = util.ensure_int(csv_row[self.header.index("Index Number")])
        self.output_data["SR"] = util.ensure_float(csv_row[self.header.index("SR")])
        self.output_data["Hit Dice"] = util.ensure_int(csv_row[self.header.index("Hit Dice")])
        self.output_data["MIN LVL FD"] = util.ensure_int(csv_row[self.header.index("MIN LVL FD")])
        self.output_data["HP"] = util.ensure_int(csv_row[self.header.index("HP")])
        self.output_data["AC"] = util.ensure_int(csv_row[self.header.index("AC")])
        self.output_data["Evolve"] = util.ensure_string(csv_row[self.header.index("Evolve")])

    def setup_speed(self, csv_row):
        self.output_data["WSp"] = util.ensure_int(csv_row[self.header.index("WSp")])
        self.output_data["Ssp"] = util.ensure_int(csv_row[self.header.index("Ssp")])
        self.output_data["Fsp"] = util.ensure_int(csv_row[self.header.index("Fsp")])
        self.output_data["Climbing Speed"] = util.ensure_int(csv_row[self.header.index("Climbing Speed")])
        self.output_data["Burrowing Speed"] = util.ensure_int(csv_row[self.header.index("Burrowing Speed")])

    def setup_attributes(self, csv_row):
        self.output_data["attributes"] = {}
        self.output_data["attributes"]["STR"] = util.ensure_int(csv_row[self.header.index("STR")])
        self.output_data["attributes"]["DEX"] = util.ensure_int(csv_row[self.header.index("DEX")])
        self.output_data["attributes"]["CON"] = util.ensure_int(csv_row[self.header.index("CON")])
        self.output_data["attributes"]["INT"] = util.ensure_int(csv_row[self.header.index("INT")])
        self.output_data["attributes"]["WIS"] = util.ensure_int(csv_row[self.header.index("WIS")])
        self.output_data["attributes"]["CHA"] = util.ensure_int(csv_row[self.header.index("CHA")])

    def setup_abilities(self, csv_row):
        self.output_data["Abilities"] = []
        self.output_data["Abilities"].append(csv_row[self.header.index("Ability1")])
        self.output_data["Abilities"].append(csv_row[self.header.index("Ability2")])
        self.output_data["Hidden Ability"] = util.ensure_string(csv_row[self.header.index("HiddenAbility")])

    def setup_senses(self, csv_row):
        self.output_data["Senses"] = util.ensure_list(csv_row[self.header.index("Senses")])

    def setup_type(self, csv_row):
        self.output_data["Type"] = util.ensure_list(csv_row[self.header.index("Type")], "/")

    def setup_skill(self, csv_row):
        self.output_data["Skill"] = util.ensure_list(csv_row[self.header.index("Skill")])

    def setup_size(self, csv_row):
        self.output_data["size"] = util.ensure_string(csv_row[self.header.index("Size")])

    def setup_saving_throws(self, csv_row):
        self.output_data["saving_throws"] = []
        first_saving_throw = csv_row[self.header.index("ST1")]
        if "All" in first_saving_throw:
            self.output_data["saving_throws"] = util.ATTRIBUTES
        else:
            self.output_data["saving_throws"].append(first_saving_throw)
            self.output_data["saving_throws"].append(csv_row[self.header.index("ST2")])
            self.output_data["saving_throws"].append(csv_row[self.header.index("ST3")])
        for st in self.output_data["saving_throws"]:
            if st != "" and not (st in util.ATTRIBUTES_FULL or st in util.ATTRIBUTES):
                print(f"ValueError: Trying to add {st} to saving throw for {self.name}")

    def setup_moves(self, csv_row):
        self.output_data["Moves"] = {}
        self.output_data["Moves"]["Level"] = {}
        self.output_data["Moves"]["Starting Moves"] = []
        self.output_data["Moves"]["TM"] = []
        move_text = csv_row[self.header.index("Moves")]
        starting_moves = self.RE_STARTING_MOVES.match(move_text)
        if starting_moves:
            self.output_data["Moves"]["Starting Moves"] = util.ensure_list(starting_moves.group(1))

        lvl_moves = self.RE_LEVEL_MOVES.findall(move_text)
        if lvl_moves:
            for level, moves in lvl_moves:
                self.output_data["Moves"]["Level"][level] = [x.strip() for x in moves.split(",") if x.strip()]
        tm_moves = self.RE_TM_MOVES.search(move_text)
        if tm_moves:
            if "EVERY TM" in move_text:
                self.output_data["Moves"]["TM"] = [int(x) for x in range(1, 101)]
            else:
                self.output_data["Moves"]["TM"] = [int(x) for x in re.findall(r"[0-9]+", tm_moves.group(1))]

        egg_moves = self.RE_EGG_MOVES.search(move_text)
        if egg_moves:
            self.output_data["Moves"]["egg"] = [x.strip() for x in egg_moves.group(1).split(",") if x.strip()]

    def cleanup(self):
        util.clean_object(self.output_data["Abilities"])

        util.clean_object(self.output_data["Skill"])
        if not self.output_data["Skill"]:
            del self.output_data["Skill"]

        util.clean_object(self.output_data["saving_throws"])
        if not self.output_data["saving_throws"]:
            del self.output_data["saving_throws"]

        if not self.output_data["Moves"]["TM"]:
            del self.output_data["Moves"]["TM"]

        for level in ["2", "6", "10", "14", "18"]:
            if level in self.output_data["Moves"]["Level"] and not self.output_data["Moves"]["Level"][level]:
                del self.output_data["Moves"]["Level"][level]

    def setup(self, csv_row):
        self.name = fix_species_name(csv_row[self.header.index(POKEMON)])

        self.setup_abilities(csv_row)
        self.setup_attributes(csv_row)
        self.setup_basic_stats(csv_row)
        self.setup_moves(csv_row)
        self.setup_saving_throws(csv_row)
        self.setup_senses(csv_row)
        self.setup_skill(csv_row)
        self.setup_speed(csv_row)
        self.setup_type(csv_row)
        self.setup_size(csv_row)

        if self.name in util.MERGE_POKEMON_DATA:
            util.merge(self.output_data, util.MERGE_POKEMON_DATA[self.name])
        self.cleanup()

    def add_default_variant(self, variant_name, species_display, original_species, create_mode, permanent):
        if hasattr(self, "variant_data"):
            raise Exception("Cannot add more than 1 default variant")
        self.variant_data = {
            "create_mode" : create_mode,
            "permanent" : permanent,
            "default" : variant_name,
            "variants" : {}
        }
        self.add_variant(variant_name, species_display, original_species, None)

    def add_variant(self, variant_name, species_display, original_species, other_poke_data):
        if not hasattr(self, "variant_data"):
            raise Exception("Must add a default variant before adding additional variants")
        self.variant_data["variants"][variant_name] = {
            "display" : species_display,
            "original_species" : original_species,
        }
        if other_poke_data:
            self.variant_data["variants"][variant_name]["diff"] = util.diff_dict(self.output_data, other_poke_data.output_data)

    def save(self):
        name = clean_file_name(self.name)
        if not util.Paths.POKEMON_OUTPUT.exists():
            util.Paths.POKEMON_OUTPUT.mkdir()
        with (util.Paths.POKEMON_OUTPUT / (name + ".json")).open("w", encoding="utf-8") as fp:
            final_output_data = self.output_data
            if hasattr(self, "variant_data"):
                final_output_data["variant_data"] = self.variant_data
            json.dump(util.clean_dict(final_output_data), fp, ensure_ascii=False, indent="  ", sort_keys=True)


class Evolve:
    RE_POINTS = re.compile("gains (\d{1,2})")
    RE_LEVEL = re.compile("level (\d{1,2})")
    RE_MOVE = re.compile("'(.*)'")
    RE_HOLDING = re.compile("while holding a (.*)\.")

    def __init__(self, header, pokemon_by_name):
        self.header = header
        self.pokemon_by_name = pokemon_by_name
        self.output_data = {}

    def add(self, csv_row, poke_data):
        species = poke_data.name

        self.output_data[species] = {}
        self.output_data[species]["into"] = []
        self.output_data[species]["current_stage"] = util.ensure_int(csv_row[self.header.index("Evo Stages with Eviolite")])
        self.output_data[species]["total_stages"] = util.ensure_int(csv_row[self.header.index("Evo Stages w/o Eviolite")])
        evolve_text = csv_row[self.header.index("Evolution for sheet")]

        # Iterate all Pokemon names and see if they are in the description
        for _, poke in self.pokemon_by_name.items():
            if poke.valid and not poke.name == species and " {} ".format(poke.name) in evolve_text:
                self.output_data[species]["into"].append(poke.name)

        match = self.RE_POINTS.search(evolve_text)
        if match:
            self.output_data[species]["points"] = int(match.group(1))

        match = self.RE_LEVEL.search(evolve_text)
        if match:
            self.output_data[species]["level"] = int(match.group(1))
        else:
            self.output_data[species]["level"] = 0
            match = self.RE_MOVE.search(evolve_text)
            if match:
                self.output_data[species]["move"] = match.group(1)
            # else:
            #     match = self.RE_HOLDING.search(evolve_text)
            #     if match:
            #         self.output_data[species]["holding"] = match.group(1)

        if self.output_data[species]["current_stage"] == 1 and self.output_data[species]["total_stages"] == 1 and not self.output_data[species]["level"]:
            del self.output_data[species]

        if species in self.output_data:
            if not self.output_data[species]["level"]:
                del self.output_data[species]["level"]
            if not self.output_data[species]["into"]:
                del self.output_data[species]["into"]

        if species in util.MERGE_EVOLVE_DATA:
            util.merge(self.output_data[species], util.MERGE_EVOLVE_DATA[species])

    def save(self):
        with (util.Paths.OUTPUT / "evolve.json").open("w", encoding="utf-8") as fp:
            json.dump(self.output_data, fp, ensure_ascii=False, indent="  ")


class IndexOrder:
    def __init__(self, header):
        self.header = header
        self.output_data = {}

    def add(self, csv_row, poke_data):
        value = util.ensure_int(csv_row[self.header.index("Index Number")])
        species = poke_data.name

        if value not in self.output_data:
            self.output_data[value] = []
        self.output_data[value].append(species)

    def save(self):
        with (util.Paths.OUTPUT / "index_order.json").open("w", encoding="utf-8") as fp:
            json.dump(self.output_data, fp, ensure_ascii=False, indent="  ")


class FilterData:
    def __init__(self, header):
        self.header = header
        self.output_data = {}

    def add(self, csv_row, poke_data):
        species = poke_data.name
        if species not in self.output_data:
            self.output_data[species] = {}
        self.output_data[species]["index"] = util.ensure_int(csv_row[self.header.index("Index Number")])

        self.output_data[species]["Type"] = util.ensure_list(csv_row[self.header.index("Type")], "/")
        self.output_data[species]["SR"] = util.ensure_float(csv_row[self.header.index("SR")])
        self.output_data[species]["MIN LVL FD"] = util.ensure_int(csv_row[self.header.index("MIN LVL FD")])

        if species in util.MERGE_FILTER_DATA:
            util.merge(self.output_data[species], util.MERGE_FILTER_DATA[species])

    def save(self):
        with (util.Paths.OUTPUT / "filter_data.json").open("w", encoding="utf-8") as fp:
            json.dump(self.output_data, fp, ensure_ascii=False, indent="  ")


class VariantMap:
    def __init__(self):
        self.output_data = {}

    def add(self, poke_base_name, poke_variant_name):
        if not poke_base_name in self.output_data:
            self.output_data[poke_base_name] = [poke_variant_name]
        else:
            self.output_data[poke_base_name].append(poke_variant_name)

    def save(self):
        with (util.Paths.OUTPUT / "variant_map.json").open("w", encoding="utf-8") as fp:
            json.dump(self.output_data, fp, ensure_ascii=False, indent="  ")



def collect_variant_data(poke_by_name):
    variant_map = VariantMap()

    variant_by_species = {}
    default_poke_by_species = {}
    default_species_by_variant = {}
    # TODO: In the future we may have other variants, like Alolan forms or something.
    # It's unclear what those might look like from a data perspective
    for name, variant_poke_data in util.VARIANT_DATA.items():
        if not "create_mode" in variant_poke_data or not isinstance(variant_poke_data["create_mode"], str):
            raise Exception(f"Variant for species {name} does not specify 'create_mode' string")
        if not "permanent" in variant_poke_data or not isinstance(variant_poke_data["permanent"], bool):
            raise Exception(f"Variant for species {name} does not specify 'permanent' bool")
        if not "variants" in variant_poke_data or not isinstance(variant_poke_data["variants"], list):
            raise Exception(f"Variant for species {name} does not specify 'variants' list")

        for this_variant_data in variant_poke_data["variants"]:
            if this_variant_data["name"] in poke_by_name:

                poke = poke_by_name[this_variant_data["name"]]
                if "default" in this_variant_data and this_variant_data["default"]:
                    poke.name = name

                    species_display = this_variant_data["species_display"] if "species_display" in this_variant_data else this_variant_data["name"]
                    original_name = this_variant_data["original_name"] if "original_name" in this_variant_data else this_variant_data["name"]

                    poke.add_default_variant(this_variant_data["variant_name"], species_display, original_name, variant_poke_data["create_mode"], variant_poke_data["permanent"])
                    variant_map.add(name, original_name)
                    default_species_by_variant[name] = this_variant_data["name"]

                    if "sprite_suffix" in variant_poke_data:
                        poke.variant_data["sprite_suffix"] = variant_poke_data["sprite_suffix"]

                else:
                    # Store for later, after the default variant has been collected
                    variant_by_species[this_variant_data["name"]] = this_variant_data
                    default_poke_by_species[this_variant_data["name"]] = name
            else:
                raise Exception(f"When searching for variants, could not find pokemon of species {this_variant_data['name']}")

    # Merge in all the other variants
    for species, this_variant_data in variant_by_species.items():
        default_poke = poke_by_name[default_species_by_variant[default_poke_by_species[species]]]
        variant_poke = poke_by_name[species]
        variant_poke.valid = False

        species_display = this_variant_data["species_display"] if "species_display" in this_variant_data else this_variant_data["name"]
        original_name = this_variant_data["original_name"] if "original_name" in this_variant_data else this_variant_data["name"]

        default_poke.add_variant(this_variant_data["variant_name"], species_display, original_name, variant_poke)
        variant_map.add(default_poke_by_species[species], original_name)

    return variant_map


def convert_pdata(input_csv, header=DEFAULT_HEADER):
    with open(input_csv, "r", encoding="utf-8") as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"')
        next(reader)
        
        poke_by_name = {}
        row_by_poke = {}

        # Collect all the rows into Pokemon types
        for index, row in enumerate(reader, 1):
            if not row:
                continue

            # Each row is one Pokemon
            poke = Pokemon(header)
            poke.setup(row)
            poke_by_name[poke.name] = poke
            row_by_poke[poke] = row
        if util.options["variants"]:
            # Some rows are variants of a single pokemon type. Let's go collect those
            variant_map = collect_variant_data(poke_by_name)

        evolve = Evolve(header, poke_by_name)
        filter_data = FilterData(header)
        index_order = IndexOrder(header)

        for name, poke in poke_by_name.items():
            if poke.valid:
                poke.save()
                
                row = row_by_poke[poke]
                evolve.add(row, poke)
                filter_data.add(row, poke)
                index_order.add(row, poke)

        if util.options["variants"]:
            variant_map.save()
        evolve.save()
        filter_data.save()
        index_order.save()


if __name__ == '__main__':
    convert_pdata(util.Paths.DATA / "PDATA.csv")
