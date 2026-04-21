import copy

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
    if space["w"] > box.w:
        new_spaces.append({
            "x": space["x"],
            "y": space["y"],
            "z": space["z"] + box.h,
            "l": space["l"],
            "w": space["w"],
            "h": space["h"] - box.h
        })

    return new_spaces

def boxPacking(boxes, truck):
    placed = []

    free_spaces = [
        {"x": 0, "y": 0, "z": 0, "l": truck["L"], "w": truck["W"], "h": truck["H"]}
    ]

    # Ordenar pelo peso
    boxes = sorted(boxes, key=lambda b: b.weight, reverse=True)

    for box in boxes:
        placed_flag = False

        for (l, w, h) in get_rotations(box):
            test_box = copy.copy(box)
            test_box.l, test_box.w, test_box.h = l, w, h

            for i, space in enumerate(free_spaces):

                if fits(test_box, space):

                    new_box = PlacedBox(box, space["x"], space["y"], space["z"])
                    placed.append(new_box)

                    new_spaces = remove_space(space,test_box)

                    free_spaces.pop(i)
                    free_spaces.extend(new_spaces)

                    placed_flag = True
                    print(f"Box {box.id}: -> L: {test_box.l}, W: {test_box.w}, H: {test_box.h}")
                    break

            if placed_flag:
                break

        if not placed_flag:
            print(f"Box {box.id} não foi colocada")

    return placed

if __name__ == "__main__":
    truck = {"L": 70, "W": 70, "H": 100}

    boxes = [
        Box(1, 50, 40, 30, 20, "metal"),
        Box(2, 30, 30, 60, 5, "glass"),
        Box(3, 40, 40, 40, 15, "cardboard"),
        Box(4, 60, 50, 20, 25, "metal"),
    ]

    result = boxPacking(boxes, truck)

    for b in result:
        print(f"Box {b.id} -> X: {b.x}, Y: {b.y}, Z: {b.z}")