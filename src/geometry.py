import math

import matplotlib.pyplot as plt


class GeometryPlotter:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect('equal')
        self.points = {
            "A": (0, 0),
            "B": (2, 4),
            "C": (5, 0)
        }
        self.lines = []

    def execute_commands(self, commands: list):
        define_cmds = [c for c in commands if c.get("command") == "DEFINE"]
        action_cmds = [c for c in commands if c.get("command") in ["CONSTRUCT", "CALCULATE"]]

        for cmd in define_cmds:
            if cmd.get("entity") == "triangle":
                self._setup_triangle(cmd)

        for cmd in action_cmds:
            self._construct_element(cmd)

    def _setup_triangle(self, cmd):
        specs = cmd.get("params", {}).get("specifications", [])
        label = cmd.get("label", "ABC")

        v1, v2, v3 = label[0], label[1], label[2]

        if "isosceles" in specs:
            self.points[v1] = (0, 0)
            self.points[v2] = (3, 5)
            self.points[v3] = (6, 0)
        elif "right" in specs:
            self.points[v1] = (0, 0)
            self.points[v2] = (0, 4)
            self.points[v3] = (5, 0)
        elif "equilateral" in specs:
            self.points[v1] = (0, 0)
            self.points[v2] = (3, 3 * math.sqrt(3))
            self.points[v3] = (6, 0)
        else:
            self.points[v1] = (0, 0)
            self.points[v2] = (2, 5)
            self.points[v3] = (7, 0)

        self.lines.append((v1, v2, "black"))
        self.lines.append((v2, v3, "black"))
        self.lines.append((v3, v1, "black"))

    def _construct_element(self, cmd):
        entity = cmd.get("entity")
        label = cmd.get("label")
        params = cmd.get("params", {})

        if entity == "point":
            segment = params.get("on_segment")
            if segment and len(segment) == 2:
                p1_n, p2_n = segment[0], segment[1]

                if p1_n in self.points and p2_n in self.points:
                    x1, y1 = self.points[p1_n]
                    x2, y2 = self.points[p2_n]

                    t = 0.35
                    nx = x1 + t * (x2 - x1)
                    ny = y1 + t * (y2 - y1)

                    point_name = label if label else "W"

                    self.points[point_name] = (nx, ny)
            return

        if not label: return

        if entity == "segment":
            if len(label) == 2:
                s, e = label[0], label[1]
                if s in self.points and e in self.points:
                    self.lines.append((s, e, "black"))
                    pass
            return

        start_name = label[0]
        end_name = label[1] if len(label) > 1 else None

        if start_name not in self.points: return

        others = [k for k in self.points if k != start_name]
        if len(others) < 2: return

        p1_name, p2_name = others[0], others[1]
        p1 = self.points[p1_name]
        p2 = self.points[p2_name]
        start_coords = self.points[start_name]

        target_x, target_y = 0, 0
        color = "black"

        if entity == "median":
            target_x = (p1[0] + p2[0]) / 2
            target_y = (p1[1] + p2[1]) / 2
            color = "blue"

        elif entity == "altitude":
            x0, y0 = start_coords
            x1, y1 = p1
            x2, y2 = p2

            dx, dy = x2 - x1, y2 - y1

            if dx == 0 and dy == 0: return

            t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)

            target_x = x1 + t * dx
            target_y = y1 + t * dy
            color = "red"

        elif entity == "bisector":
            len1 = math.sqrt((start_coords[0] - p1[0]) ** 2 + (start_coords[1] - p1[1]) ** 2)
            len2 = math.sqrt((start_coords[0] - p2[0]) ** 2 + (start_coords[1] - p2[1]) ** 2)

            k = len1 / len2

            target_x = (p1[0] + k * p2[0]) / (1 + k)
            target_y = (p1[1] + k * p2[1]) / (1 + k)
            color = "green"

        if end_name:
            if end_name not in self.points:
                self.points[end_name] = (target_x, target_y)

            self.lines.append((start_name, end_name, color))

    def plot(self, save_path=None):
        """Renders the plot."""
        for start, end, color in self.lines:
            if start in self.points and end in self.points:
                p1 = self.points[start]
                p2 = self.points[end]
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=2)

        for name, (x, y) in self.points.items():
            self.ax.plot(x, y, 'ko')
            self.ax.text(x + 0.1, y + 0.1, name, fontsize=12, fontweight='bold')

        plt.grid(True)
        plt.title("Рисунок до задачі")
        if save_path:
            plt.savefig(save_path)
            plt.close()
            print(f"   [SAVED] {save_path}")
        else:
            plt.show()