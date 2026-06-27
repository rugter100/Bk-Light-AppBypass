<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)](https://www.linux.org/)
[![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![BLE](https://img.shields.io/badge/BLE-4.0+-0082FC?logo=bluetooth&logoColor=white)](https://www.bluetooth.com/)
[![Bleak](https://img.shields.io/badge/Bleak-BLE%20client-3776AB)](https://github.com/hbldh/bleak)
[![Pillow](https://img.shields.io/badge/Pillow-Imaging-3776AB)](https://python-pillow.org/)
[![PyYAML](https://img.shields.io/badge/PyYAML-Config-CB0000)](https://pyyaml.org/)

</div>

# BLE LED Display Webinterface

Web based utility for controlling BK-Light RGB LED matrices over BLE, **Supported panels:** 32×32 (ACT1026). (more support planned)

This tool is very much WIP and the code on main or dev is very much not stable or reliable, use/try out at your own risk

Currently full control of each pixel using webAPI via its endpoints: 
 - POST `/setpixel/<panel_id>` set a pixel or multiple seperate pixels colour
   - Json:
   - `data_type': '<single/multi>'`
   - Single: `'data': {'x': <int>, 'y': <int>, 'color': [<int 0-255>, <int 0-255>, <int 0-255>]}`
   - Multi: `'data': {'<x-coord Int>': {'<y-coord Int>': [<int 0-255>, <int 0-255>, <int 0-255>]}}`
 - POST `/fill/<panel_id>`  Fill a region between 2 coordinates
   - Json:
   - `{'a_coords': [<x-coord Int>, <y-coord Int>], 'b_coords': [<same as a_coords>], 'color': [<int 0-255>, <int 0-255>, <int 0-255>]}`
 - POST `/write/<panel_id>` Write text
   - Json:
   - `{'coords': [<x-coord Int>, <y-coord Int>], 'text': '<Str>', Optional> 'font_name': <Str>, 'color': [<int 0-255>, <int 0-255>, <int 0-255>], 'bg_color': [<int 0-255>, <int 0-255>, <int 0-255>], 'wrap': True/False, 'spacing': <int>}`
 - POST `/multitool/<panel_id>` Combination of setpixel, fill and write
   - Json:
   - `{'write': {<write objects>}, 'fill': {<fill objects>}, 'setpixel': {<setpixel objects>}, 'print_order': <order list>}`
   - `Order List: {'<Int>': ['write', <key>], '<Int>': ['fill', <key>], '<Int>': ['write', <key>], '<Int>': ['setpixel', <key>]}` (will be sorted numerically by the server)
 - GET `/blackout/<panel_id>` Blacks out panel
 - GET `/getstatuis/<panel_id>` Gets status of connection, responds with bool or list of bools depending on if the id is a specific panel or a panel group
 - GET `/get_grid/<panel_id>` Gets the entire grid list of selected panel (!Large dataset!)
 - GET `/health` Simple check to see if webserver is online and reachable
(Better api docs are coming)


This project has originally been forked from https://github.com/Pupariaa/Bk-Light-AppBypass, part of this readme has been kept due to having similar requirements and debug steps. All credits for reverse engineering the bluetooth protocol go to this repo and its contributors

## Requirements

- Python 3.13+
- `pip install bleak Pillow PyYAML`
- Bluetooth adapter with BLE support enabled
- Hardware capabilities:
  - BLE 4.0 or newer with GATT/ATT support
  - Central role / GATT client mode
  - LE 1M PHY
  - Long ATT write support (Prepare/Execute or Write-with-response handling for fragmented payloads)
  - MTU negotiation and L2CAP fragmentation

The tools assume the screen advertises as `LED_BLE_*` (BK-Light firmware). Update the MAC address in `config.yml` (or via `BK_LIGHT_ADDRESS`) if your unit differs. (currently auto detection is not implemented yet)

## Acknowledgment (Windows / Python 3.13)

If you see `ModuleNotFoundError: No module named 'bleak'` or `ModuleNotFoundError: No module named 'PIL'` after `pip install -r requirements.txt`, or a **LNK1104** / failed wheel build for `winrt-Windows.Devices.Bluetooth.GenericAttributeProfile`, you are likely using the **free-threaded** Python 3.13 build (`python3.13t`). Bleak’s Windows dependencies (winrt) do not ship pre-built wheels for that variant, so pip tries to compile them and the build often fails.

Use the **standard** Python 3.13 (not the “t” build) for this project. Example:

```powershell
py -3.13 -m pip install -r requirements.txt
py -3.13 .\scripts\production.py
```

If `py -3.13` is not available, install the non–free-threaded Python 3.13 from [python.org](https://www.python.org/downloads/) and use that interpreter for install and run.

## Project Structure

- `config.yml` – WebAPI config, panel id list and grouping
- `web.py` – Script to run, this will load all the dependencies and start the webserver
- `webtest.py` – Script to test your panels (adjust the python code according to your use case)

## Quick Start

1. Install dependencies:

   ```bash
   pip install bleak Pillow PyYAML flask werkzeug waitress
   ```

2. Edit `config.yml`.

  add your panel addresses to the panels and adjust network settings if needed (auto panel detect is coming)

3. Run web.py
  
  ```bash
  python3 web.py
  ```
4. Access the panel

  Using the API endpoints you can control the panels to set data to it, which is accessible on its configured ip:port

## Attribution & License

- Communication and translation to BK-Light panel created by Puparia — GitHub: [Pupariaa](<https://github.com/Pupariaa>).
- WebAPI and grid system created by Marijeeee — GitHub: [Marije](<https://github.com/rugter100>)
- Code is open-source but contributions are currently closed due to the base of the code not being finished yet.
- Originally forked from https://github.com/Pupariaa/Bk-Light-AppBypass
- Licensed under the [MIT License](./LICENSE).
