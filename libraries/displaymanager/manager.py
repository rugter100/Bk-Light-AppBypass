import asyncio
import yaml
from .printer import Print

PANEL_W = 32
PANEL_H = 32


class VirtualGrid:
    def __init__(self, manager, group_map):
        self.manager = manager
        self.group_map = group_map  # {(gx,gy): panel_id}

    def __setitem__(self, pos, color):
        x, y = pos

        # convert global pixel → group coordinates
        panel_x = x // PANEL_W
        panel_y = y // PANEL_H

        local_x = x % PANEL_W
        local_y = y % PANEL_H

        panel_id = self.group_map.get((panel_x, panel_y))
        if panel_id is None:
            return  # outside group

        self.manager.displays[panel_id].grid[local_y][local_x] = color


class GroupHandle:
    def __init__(self, manager, group_map):
        self.manager = manager
        self.group_map = group_map
        self.grid = VirtualGrid(manager, group_map)


class DisplayManager:
    def __init__(self, config_path="config.yml"):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.displays = {}
        self.groups = {}
        self.group_handles = {}

        for panel_id, address in config["panels"].items():
            self.displays[int(panel_id)] = Print(address)

    def __getitem__(self, key):
        try:
            key = int(key)
        except (TypeError, ValueError):
            pass

        if isinstance(key, int):
            return self.displays[key]

        if isinstance(key, str):
            if key not in self.group_handles:
                raise KeyError(f"Group '{key}' does not exist")
            return self.group_handles[key]

        raise TypeError("Key must be int (panel) or str (group)")

    @property
    def group(self):
        return self.group_handles

    def panels(self, ids):
        """Return list of Print objects for given IDs"""
        return [self.displays[i] for i in ids]

    async def send(self, key):
        try:
            key = int(key)
        except (TypeError, ValueError):
            pass

        if isinstance(key, int):
            await self.displays[key].send_grid()

        elif isinstance(key, str):
            if key in self.group_handles:
                group = self.groups[key]
                await asyncio.gather(*(self.displays[i].send_grid() for i in group.values()))
                return

            raise KeyError(f"Unknown group '{key}'")

        elif isinstance(key, list):
            await asyncio.gather(
                *(self.displays[i].send_grid() for i in key)
            )

    def get_group(self, name):
        return [self.displays[i] for i in self.groups[name].values()]

    def create_group(self, name, mapping: dict):
        # mapping: {(x,y): panel_id}
        # (gx, gy): panel_id

        # ---- 1. validate panels exist
        for panel_id in mapping.values():
            if panel_id not in self.displays:
                raise ValueError(f"Panel {panel_id} does not exist")

        # ---- 2. extract coordinates
        coords = list(mapping.keys())
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # ---- 3. enforce rectangle (NO holes allowed)
        expected = set(
            (x, y)
            for x in range(min_x, max_x + 1)
            for y in range(min_y, max_y + 1)
        )

        if set(coords) != expected:
            missing = expected - set(coords)
            raise ValueError(
                f"Group '{name}' is not a complete rectangle. Missing: {missing}"
            )

        self.groups[name] = mapping

        self.group_handles[name] = GroupHandle(self, mapping)
