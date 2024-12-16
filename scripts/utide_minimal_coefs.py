from coef import coef
from utide import reconstruct
import pandas as pd

t = pd.date_range("2000", periods=10, freq="h")

tide = reconstruct(t, coef)

print(tide["h"])
