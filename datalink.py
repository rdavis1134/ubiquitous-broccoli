import typing
import json


#   JSON handling functions


def fetch_json(file: str) -> typing.Dict:
    try:
        with open(file, 'r') as f:
            try:
                result = json.load(f)
            except ValueError as err:
                print(err)
                result = {}
            except FileNotFoundError:
                result = {}
    except FileNotFoundError:   # Apparently the inner FileNotFoundError isn't enough.
        result = {}             # I guess the with() fails terminally as well. What a waste.
    return result


def save_json(file: str, data: typing.Dict):
    with open(file, 'w') as f:  # This with() also fails terminally if the data folder doesn't exist.
        result = json.dumps(data, indent=4)
        f.write(result)

