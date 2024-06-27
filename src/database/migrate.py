import json
from pprint import pprint
from typing import Dict

"""
"0x77a298bf902001a": {
            "cash": 3535.0,
            "stocks": {
                "AAPL": {
                    "stocks_owned": 13.75716825743435,
                    "valued_invested": 125
                },
                "TSLA": {
                    "stocks_owned": 2.546418228512103,
                    "valued_invested": 125
                }
            }
        }
"""


def load_data(file_path) -> Dict[str, Dict]:
    if file_path is None:
        return {}
    
    with open(file_path, 'r') as f:
        raw_data: dict = json.load(f)

    # pprint(raw_data)
    return raw_data

def save_data(file_path, data):        
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def changes(data):

    for i in data:
        for j in data[i]:
            for k in data[i][j]['stocks']:
                data[i][j]['stocks'][k] = {
                    "number_owned": data[i][j]['stocks'][k],
                    "valued_invested": 0
                }
            
    return data


def main():
    data = load_data("../data.json")

    pprint(data)    
    changes(data)
    pprint(data)
    
    save_data("../new_data.json", data)
    

if __name__ == '__main__':
    main()
