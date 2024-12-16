import numpy as np

coef = {
    "name": [  # some names of consituents, used for subselection
        "K1",
        "K2",
        "M2",
        "M4",
        "MF",
        "MM",
        "MN4",
        "MS4",
        "N2",
    ],  # 'O1', 'P1', 'Q1', 'S2'],
    "mean": 0.0,
    "A": np.array(  # amplitudes
        [
            1.00227454,
            0.02250278,
            0.01775812,
            0.01605451,
            0.01220086,
            0.00751468,
            0.00708371,
            0.00577484,
            0.00313313,
        ]
    ),
    "g": np.array(  # phases
        [
            139.03197411,
            144.78007052,
            117.14151752,
            104.1430418,
            216.82454621,
            4.40876086,
            240.44658427,
            50.66603851,
            144.04531879,
        ]
    ),
    "aux": {
        "opt": {
            "twodim": False,  # False for level
            "nodiagn": True,
            "nodsatlint": 0,
            "nodsatnone": True,
            "gwchlint": False,
            "gwchnone": False,
            "prefilt": np.array([]),
            "notrend": True,  # don't use trend
        },
        "reftime": 737429.1458333333,  # reference time in days since ?
        "frq": np.array(  # frequencies in cycles per hour
            [
                0.0805114,  # M2
                0.04178075,  # ?
                0.3220456,
                0.20280355,
                0.1207671,
                0.28331495,
                0.1610228,
                0.2415342,
                0.20844741,
            ]
        ),
        "lat": -42.5,  # latitude
        "lind": np.array(
            [47, 20, 124, 95, 68, 119, 81, 105, 98]
        ),  # list indices of constituents in ut_constants.mat (nc x 1)
    },
}
