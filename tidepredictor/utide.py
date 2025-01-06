import os
import numpy as np
import toml
from dataclasses import dataclass
from typing import Any


@dataclass
class Coef:
    name: list[str]
    mean: float
    A: np.ndarray
    g: np.ndarray
    aux: dict[str, Any]  # TODO exctract aux to a separate dataclass

    def __post_init__(self):
        assert len(self.A) == len(self.g) == len(self.name) == len(self.aux["frq"])

    @staticmethod
    def _convert_data(data: dict[str, Any]) -> dict[str, Any]:
        data["A"] = np.array(data["A"])
        data["g"] = np.array(data["g"])
        data["aux"]["opt"]["prefilt"] = np.array(data["aux"]["opt"]["prefilt"])
        data["aux"]["frq"] = np.array(data["aux"]["frq"])
        data["aux"]["lind"] = np.array(data["aux"]["lind"])
        return data

    @staticmethod
    def from_toml(file_path: str) -> "Coef":
        with open(file_path, "r") as file:
            data = toml.load(file)
        data = Coef._convert_data(data)
        return Coef(**data)


if __name__ == "__main__":
    curdir = os.path.dirname(__file__)
    fp = os.path.join(curdir, "coef.toml")

    coef = Coef.from_toml(fp)
    print(coef)
