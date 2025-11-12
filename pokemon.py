import csv
import json

# Define file paths
a_csv_file = './dataset/csv/pokemon.csv'
b_csv_file = './dataset/csv/pokemon_hasForm_form.csv'
c_csv_file = './dataset/csv/form.csv'
d_csv_file = './dataset/csv/pokemon_evolvesTo_pokemon.csv'
e_csv_file = './dataset/csv/pokemon_hasType_type.csv'
output_json_file = './pokemon.json'

with open(a_csv_file, mode='r', newline='', encoding='utf-8') as file_a:
    reader_a = csv.DictReader(file_a)
    a_rows = list(reader_a)

with open(b_csv_file, mode='r', newline='', encoding='utf-8') as file_b:
    reader_b = csv.DictReader(file_b)
    b_rows = list(reader_b)

with open(c_csv_file, mode='r', newline='', encoding='utf-8') as file_c:
    reader_c = csv.DictReader(file_c)
    c_rows = list(reader_c)

with open(d_csv_file, mode='r', newline='', encoding='utf-8') as file_d:
    reader_d = csv.DictReader(file_d)
    d_rows = list(reader_d)

with open(e_csv_file, mode='r', newline='', encoding='utf-8') as file_e:
    reader_e = csv.DictReader(file_e)
    e_rows = list(reader_e)

has_form = {}
form = {}

pokemons = {}

for row_a in a_rows:
    pokemons[row_a['id']] = row_a['pokename']

for row_c in c_rows:
    form[row_c['id']] = row_c['form']

for row_b in b_rows:
    has_form[pokemons[row_b['pokemonID']]] = [form[row_b['formID']], row_b['pokemonID']]

evolves_to = {}

for row_d in d_rows:
    evolves_to[row_d['primitiveID']] = row_d['evolvedID']

has_type = {}

for row_e in e_rows:
    if (row_e['pokemonID'] in has_type):
        has_type[row_e['pokemonID']].append(row_e['typeID'])
    else:
        has_type[row_e['pokemonID']] = [row_e['typeID']]

combined_data = []
checklist = {}

for row_a in a_rows:
    entity = {
        '_id': row_a["id"],
        'pokedex': row_a["number"],
        'name': (has_form[row_a["pokename"]][0] if row_a["pokename"] in checklist else row_a["pokename"]),
        'stats': {
            'hp': row_a["hp"],
            'atk': row_a["attack"],
            'def': row_a["defense"],
            'sp_atk': row_a["sp_atk"],
            'sp_def': row_a["sp_def"],
            'tot': row_a["total"]
        },
        'types': has_type[row_a["id"]],
        'evolves_to': (evolves_to[row_a["id"]] if row_a["id"] in evolves_to else "null"),
        'has_form': (has_form[row_a["pokename"]][1] if ((row_a["pokename"] in has_form) and not row_a["pokename"] in checklist) else "null")
    }
    checklist[row_a["pokename"]] = 1
    combined_data.append(entity)

with open(output_json_file, 'w', encoding='utf-8') as json_file:
    json.dump(combined_data, json_file, ensure_ascii=False, indent=4)
