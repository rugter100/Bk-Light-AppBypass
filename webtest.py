import time
import yaml
import requests # Not listed in requirements.txt since this is purely a devtool
import sys

from random import randint


ip = "192.168.100.15"
panel_id = "display1"

response = requests.get(f"http://{ip}:5000/scan", headers={'X-API-Token': 'my-secret-token'})
print(response.json())
sys.exit()

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)
    for panel in config["panels"]:
        response = requests.get(f"http://{ip}:5000/getstatus/{panel}",
                                 headers={'X-API-Token': 'my-secret-token'})

        print(response.json())

response = requests.post(f"http://{ip}:5000/write/{panel_id}?clear=true&update=true",
                         headers={'X-API-Token': 'my-secret-token'},
                         json={'coords': [0, 0], 'text': '987+5485=7412', 'wrap': True, 'spacing': 1})

print(response.json())
time.sleep(2)

count = 0
while count <= 10:
    response = requests.post(f"http://{ip}:5000/fill/{panel_id}?update=true&clear=true", headers={'X-API-Token': 'my-secret-token'},
                  json={'a_coords': [0, 0], 'b_coords': [randint(1, 63), randint(1, 63)], 'color': [randint(22, 255), randint(22, 255), randint(22, 255)]})
    print(response.json())
    count += 1

response = requests.post(f"http://{ip}:5000/fill/{panel_id}?update=true&clear=true", headers={'X-API-Token': 'my-secret-token'},
                         json={'a_coords': [0, 0], 'b_coords': [63, 63], 'color': [255, 255, 255]})
print(response.json())

time.sleep(2)

response = requests.post(f"http://{ip}:5000/multitool/{panel_id}?update=true&clear=true", headers={'X-API-Token': 'my-secret-token'},
                  json={'write':
                            {'write1':
                                 {'coords': [0, 0], 'text': 'Test Text 1', 'wrap': False, 'spacing': 1},
                             'write2':
                                 {'coords': [0, 10], 'text': 'Test Text 2', 'wrap': True, 'spacing': 1}},
                        'fill':
                            {'fill1':
                                 {'a_coords': [0, 20], 'b_coords': [10,40], 'color': [randint(22, 255), randint(22, 255), randint(22, 255)]}},
                        'setpixel':
                            {'setpixel1':
                                 {'data_type': 'single', 'data': {'x': 30, 'y': 30, 'color': [255, 128, 64]}}
                             }
                        })

print(response.json())

response = requests.get(f"http://{ip}:5000/getgrid/{panel_id}",
                         headers={'X-API-Token': 'my-secret-token'},)

print(response.json())


time.sleep(10)
response = requests.get(f"http://{ip}:5000/blackout/{panel_id}?update=true", headers={'X-API-Token': 'my-secret-token'})
print(response.json())
