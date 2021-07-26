#!/usr/bin/env python3

import numpy as np
import pandas as pd
from algorithms.utastar import *


multicrit_tbl = pd.read_csv("tests/cars.csv", index_col=0)
multicrit_tbl.sort_values(by=["Διάταξη"], axis=0, inplace=True)
crit_monot = {
    "Τιμή": False,
    "Κόστος Κυκλοφορίας ανά km": False,
    "Ετήσιο κόστος ιδιοκτησίας": False,
    "Ασφάλεια": True,
    "Άνεση": True,
}
a_split = {
    "Τιμή": 5,
    "Κόστος Κυκλοφορίας ανά km": 5,
    "Ετήσιο κόστος ιδιοκτησίας": 5,
    "Ασφάλεια": 5,
    "Άνεση": 5,
}
