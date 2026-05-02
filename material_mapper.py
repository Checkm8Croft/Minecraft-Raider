def map_material(m):

    MAP = {
        "TeOp_0_0": "stone_bricks",
        "TeOp_0_1": "mossy_stone_bricks",
        "TeOp_0_2": "sandstone",
        "TeOp_0_3": "smooth_stone",
        "TeOp_0_4": "bricks",
        "TeOp_0_5": "gray_concrete"
    }

    return MAP.get(m, "smooth_stone")