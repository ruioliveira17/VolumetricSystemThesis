import copy
import plotly.graph_objects as go

class Box:
    def __init__(self, id, l, w, h, weight, material):
        self.id = id
        self.l = l
        self.w = w
        self.h = h
        self.weight = weight
        self.material = material

class PlacedBox(Box):
    def __init__(self, box, x, y, z):
        super().__init__(box.id, box.l, box.w, box.h, box.weight, box.material)
        self.x = x
        self.y = y
        self.z = z

RULES = {
    "glass": {"max_weight_on_top": 5},
    "cardboard": {"max_weight_on_top": 20},
    "metal": {"max_weight_on_top": 100}
}

def get_rotations(box):
    # A função set não duplica rotações possíveis
    return list(set([
        (box.l, box.w, box.h),
        (box.l, box.h, box.w),
        (box.w, box.l, box.h),
        (box.w, box.h, box.l),
        (box.h, box.l, box.w),
        (box.h, box.w, box.l),
    ]))

def fits(box, space):
    return box.l <= space["l"] and box.w <= space["w"] and box.h <= space["h"]

def remove_space(space, box):
    new_spaces = []

    # Espaço disponível em X
    if space["l"] > box.l:
        new_spaces.append({
            "x": space["x"] + box.l,
            "y": space["y"],
            "z": space["z"],
            "l": space["l"] - box.l,
            "w": box.w,
            "h": space["h"]
        })

    # Espaço disponível em Y
    if space["w"] > box.w:
        new_spaces.append({
            "x": space["x"],
            "y": space["y"] + box.w,
            "z": space["z"],
            "l": space["l"],
            "w": space["w"] - box.w,
            "h": space["h"]
        })

    # Espaço disponível em Z
    if space["h"] > box.h:
        new_spaces.append({
            "x": space["x"],
            "y": space["y"],
            "z": space["z"] + box.h,
            "l": space["l"],
            "w": space["w"],
            "h": space["h"] - box.h
        })

    return new_spaces

def respects_weight(new_box, placed_boxes):
    for b in placed_boxes:
        if (
            abs((b.z + b.h) - new_box.z) < 1e-6 and
            not (
                b.x + b.l <= new_box.x or
                b.x >= new_box.x + new_box.l or
                b.y + b.w <= new_box.y or
                b.y >= new_box.y + new_box.w
            )
        ):
            max_allowed = RULES[b.material]["max_weight_on_top"]

            if new_box.weight > max_allowed:
                return False

    return True

def has_support(new_box, placed_boxes):
    if new_box.z == 0:
        return True

    base_area = new_box.l * new_box.w
    supported_area = 0

    for b in placed_boxes:
        if abs((b.z + b.h) - new_box.z) < 1e-6:

            overlap_x = max(0, min(new_box.x + new_box.l, b.x + b.l) - max(new_box.x, b.x))
            overlap_y = max(0, min(new_box.y + new_box.w, b.y + b.w) - max(new_box.y, b.y))

            supported_area += overlap_x * overlap_y

    return supported_area >= 0.7 * base_area

def boxPacking(boxes, truck):
    placed = []

    free_spaces = [
        {"x": 0, "y": 0, "z": 0, "l": truck["L"], "w": truck["W"], "h": truck["H"]}
    ]

    # Ordenar pelo peso
    #boxes = sorted(boxes, key=lambda b: b.w * b.l * b.h , reverse=True)
    boxes = sorted(boxes, key=lambda b: b.weight, reverse=True)

    for box in boxes:
        best_fit = None
        best_score = float("inf")

        for (l, w, h) in get_rotations(box):
            test_box = copy.copy(box)
            test_box.l, test_box.w, test_box.h = l, w, h

            for space in free_spaces:
                if fits(test_box, space):
                    temp_box = PlacedBox(test_box, space["x"], space["y"], space["z"])

                    if not respects_weight(temp_box, placed):
                        continue

                    if not has_support(temp_box, placed):
                        continue

                    max_x = max([b.x + b.l for b in placed] + [temp_box.x + temp_box.l])
                    max_y = max([b.y + b.w for b in placed] + [temp_box.y + temp_box.w])
                    max_z = max([b.z + b.h for b in placed] + [temp_box.z + temp_box.h])

                    score = max_x * max_y * max_z

                    if score < best_score:
                        best_score = score
                        best_fit = (test_box, space)

        if best_fit:
            test_box, space = best_fit

            new_box = PlacedBox(test_box, space["x"], space["y"], space["z"])
            placed.append(new_box)

            new_free_spaces = []

            for s in free_spaces:
                if not (
                    s["x"] < new_box.x + new_box.l and
                    s["x"] + s["l"] > new_box.x and
                    s["y"] < new_box.y + new_box.w and
                    s["y"] + s["w"] > new_box.y and
                    s["z"] < new_box.z + new_box.h and
                    s["z"] + s["h"] > new_box.z
                ):
                    new_free_spaces.append(s)

                else:
                    split_spaces = remove_space(s, test_box)
                    new_free_spaces.extend(split_spaces)

            free_spaces = new_free_spaces

            print(f"Box {box.id}: -> L: {test_box.l}, W: {test_box.w}, H: {test_box.h}")

        else:
            print(f"Box {box.id} não foi colocada")

    return placed

def plot_boxes(boxes, truck):
    fig = go.Figure()

    for b in boxes:
        fig.add_trace(go.Mesh3d(
            x=[b.x, b.x+b.l, b.x+b.l, b.x, b.x, b.x+b.l, b.x+b.l, b.x],
            y=[b.y, b.y, b.y+b.w, b.y+b.w, b.y, b.y, b.y+b.w, b.y+b.w],
            z=[b.z, b.z, b.z, b.z, b.z+b.h, b.z+b.h, b.z+b.h, b.z+b.h],
            opacity=1,
            alphahull=0
        ))

    # opcional: desenhar limites do camião
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[0, truck["L"]]),
            yaxis=dict(range=[0, truck["W"]]),
            zaxis=dict(range=[0, truck["H"]])
        )
    )

    fig.show()

if __name__ == "__main__":
    truck = {"L": 70, "W": 70, "H": 100}

    boxes = [
        Box(1, 50, 40, 30, 20, "metal"),
        Box(2, 30, 30, 60, 5, "glass"),
        Box(3, 40, 40, 40, 15, "cardboard"),
        Box(4, 60, 50, 20, 25, "metal"),
        Box(5, 15, 10, 5, 10, "metal"),
        Box(6, 10, 40, 20, 8, "glass"),
        Box(7, 10, 80, 30, 5, "cardboard"),
        Box(8, 10, 10, 5, 15, "metal"),
    ]

    result = boxPacking(boxes, truck)

    for b in result:
        print(f"Box {b.id} -> X: {b.x}, Y: {b.y}, Z: {b.z}")

    plot_boxes(result, truck)
