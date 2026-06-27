import base64
import json
import logging
import asyncio
import threading
from importlib import reload

#from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, render_template, abort, url_for, redirect, flash, jsonify
from functools import wraps
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.interval import IntervalTrigger

import libraries.logger as logger
from libraries.displaymanager.manager import DisplayManager

log = logger.fileLogger()
log.initialize('Main')
log.info("Logging Initialized!")

app = Flask(__name__)

# Create a scheduler instance
# scheduler = BackgroundScheduler(daemon=True)

# apscheduler_logger = logging.getLogger('apscheduler')
# apscheduler_logger.setLevel(logging.ERROR)  # Hide warnings & info from APScheduler internals

API_TOKEN = "my-secret-token"

loop = asyncio.new_event_loop()
manager = DisplayManager("config.yml")

manager.create_group("display1", {(0,0): 0, (1,0): 1})


def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=start_loop, daemon=True).start()


# Authentication Decorator
def require_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-API-Token")

        if token is None or token != API_TOKEN:
            return jsonify({
                "success": False,
                "error": "Forbidden"
            }), 403

        return func(*args, **kwargs)

    return wrapper


# API Endpoints

@app.route("/getstatus/<type>/<panel_id>", methods=["GET"])
@require_token
def get_status(type, panel_id):
    # Function to return data about current connected panels and such
    return jsonify({"success": True, 'type': type, 'panel_id': panel_id}), 200


@app.route("/blackout/<panel_id>", methods=["GET"])
@require_token
def blackout(type, panel_id):
    async def update():
        manager[panel_id].grid.clear()
        await manager[panel_id].send_grid()
        return {"success": True}

    func = asyncio.run_coroutine_threadsafe(update(), loop)

    func_res = func.result()

    return jsonify(func_res), 200

# Sets pixel, options are single or multiple:
# /setpixel?clear=true
@app.route("/setpixel/<panel_id>", methods=["POST"])
@require_token
def setpixel(panel_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Missing JSON body"
        }), 400

    if "data_type" not in data or "data" not in data:
        return jsonify({
            "success": False,
            "error": "Missing required fields"
        }), 400

    async def update():
        log.info("Updating Grid")
        if request.args.get('clear') == "true":
            manager[panel_id].grid.clear()
        if data['data_type'] == 'single':
            # Dict looks like: {'data_type': 'single', 'data': {'x': 10, 'y': 15, 'color': [255, 128, 64]}}
            manager[panel_id].grid[data['data']['x']][data['data']['y']] = tuple(data['data']['color'])
        elif data['data_type'] == 'multi':
            # Dict looks like: {'data_type': 'multi', 'data': {'1': {'1': [64, 64, 64], '5': [64, 64, 64]}, '5': {'1': [64, 64, 64], '5', [64, 64, 64]}}}
            # This makes it so that each entry in data is an X coord and each entry in the X coord is its Y coord
            try:
                for x, y_data in data['data'].items():
                    for y, color in y_data.items():
                        manager[panel_id].grid[int(x)][int(y)] = tuple(color)
            except ValueError as err:
                return {"success": False, "error": f"Malformed Json '{err}'"}
        else:
            return {"success": False, "error": f"Unknown data type '{data['data_type']}'"}
        if request.args.get('update') == "true":
            await manager[panel_id].send_grid()
        return {"success": True}

    func = asyncio.run_coroutine_threadsafe(update(), loop)

    func_res = func.result()

    return jsonify(func_res), 200

@app.route("/fill/<panel_id>", methods=["POST"])
@require_token
def fill_region(panel_id):
    # Expected Dict: {'a_coords': [<int>, <int>], 'b_coords': [<int>, <int>], 'color': [<int>, <int>, <int>]}
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Missing JSON body"
        }), 400

    if "a_coords" not in data or "b_coords" not in data or "color" not in data:
        return jsonify({
            "success": False,
            "error": "Missing required fields"
        }), 400

    async def update():
        if request.args.get('clear') == "true":
            manager[panel_id].grid.clear()
        manager[panel_id].grid.fill_rect(data['a_coords'][0], data['a_coords'][1], data['b_coords'][0], data['b_coords'][1], data['color'])
        if request.args.get('update') == "true":
            await manager[panel_id].send_grid()
        return {"success": True}

    func = asyncio.run_coroutine_threadsafe(update(), loop)

    func_res = func.result()

    return jsonify(func_res), 200

@app.route("/write/<panel_id>", methods=["POST"])
@require_token
def write(panel_id):
    # Expected dict: {'coords': [10, 1], 'text': 'text goes here'}
    # Optional Keys: 'font_name': <str>, 'color': [<int>, <int>, <int>], 'bg_color': [<int>, <int>, <int>], 'spacing': <int>, 'wrap': <bool>
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Missing JSON body"
        }), 400

    if "coords" not in data or "text" not in data:
        return jsonify({
            "success": False,
            "error": "Missing required fields"
        }), 400

    optional_keys = ['font_name', 'color', 'bg_color', 'spacing', 'wrap']
    args = {'x': data['coords'][0], 'y': data['coords'][1], 'text': data['text']}
    for key in optional_keys:
        if key in data.keys():
            args[key] = data[key]
    async def update():
        if request.args.get('clear') == "true":
            manager[panel_id].grid.clear()
        manager[panel_id].grid.draw_text(**args)
        if request.args.get('update') == "true":
            await manager[panel_id].send_grid()
        return {"success": True}

    func = asyncio.run_coroutine_threadsafe(update(), loop)

    func_res = func.result()

    return jsonify(func_res), 200

@app.route("/multitool/<panel_id>", methods=["POST"])
@require_token
def multitool(panel_id):
    # Expected Dict= {'write': {<write objects>}, 'fill': {<fill objects>}, 'setpixel': {<setpixel objects>}, 'print_order': <order list>}
    # Order List: {'0': ['write', <key>], '1': ['fill', <key>], '2': ['write', <key>], '3': ['setpixel', <key>]}
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Missing JSON body"
        }), 400

    async def update():
        def _setpixel(data_item):
            if data_item['data_type'] == 'single':
                # Dict looks like: {'data_type': 'single', 'data': {'x': 10, 'y': 15, 'color': [255, 128, 64]}}
                manager[panel_id].grid[data_item['data']['x']][data_item['data']['y']] = tuple(data_item['data']['color'])
            elif data_item['data_type'] == 'multi':
                # Dict looks like: {'data_type': 'multi', 'data': {'1': {'1': [64, 64, 64], '5': [64, 64, 64]}, '5': {'1': [64, 64, 64], '5', [64, 64, 64]}}}
                # This makes it so that each entry in data is an X coord and each entry in the X coord is its Y coord
                try:
                    for x, y_data in data_item['data'].items():
                        for y, color in y_data.items():
                            manager[panel_id].grid[int(x)][int(y)] = tuple(color)
                except ValueError as err:
                    return {"success": False, "error": f"Malformed Json '{err}'"}
            else:
                return {"success": False, "error": f"Unknown data type '{data['data_type']}'"}
            return {"success": True}

        def _fill(data_item):
            manager[panel_id].grid.fill_rect(data_item['a_coords'][0], data_item['a_coords'][1], data_item['b_coords'][0], data_item['b_coords'][1], data_item['color'])
            return {"success": True}

        def _write(data_item):
            optional_keys = ['font_name', 'color', 'bg_color', 'spacing', 'wrap']
            args = {'x': data_item['coords'][0], 'y': data_item['coords'][1], 'text': data_item['text']}
            for key in optional_keys:
                if key in data_item.keys():
                    args[key] = data_item[key]
            manager[panel_id].grid.draw_text(**args)
            return {"success": True}


        if request.args.get('clear') == "true":
            manager[panel_id].grid.clear()

        if 'print_order' in data.keys():
            sorted_order = dict(sorted(data['print_order'].items(), key=lambda item: item[0]))
            for item in sorted_order:
                if item[0] == 'setpixel':
                    _setpixel(data['setpixel'][item[1]])
                elif item[0] == 'fill':
                    _fill(data['fill'][item[1]])
                elif item[0] == 'write':
                    _write(data['fill'][item[1]])
        else:
            for item in data['write']:
                _write(data['write'][item])
            for item in data['fill']:
                _fill(data['fill'][item])
            for item in data['setpixel']:
                _setpixel(data['setpixel'][item])

        if request.args.get('update') == "true":
            await manager[panel_id].send_grid()


    func = asyncio.run_coroutine_threadsafe(update(), loop)

    func_res = func.result()

    return jsonify(func_res), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


# Error Handlers

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ==========================================================
# Run
# ==========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
