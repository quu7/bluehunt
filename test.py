#!/usr/bin/env python3

import numpy as np
import pandas as pd
from algorithms.utastar import *


multicrit_tbl = pd.read_csv("tests/public_transport.csv", index_col=0)
crit_monot = {"Τιμή": False, "Διάρκεια": False, "Άνεση": True}
a_split = {"Τιμή": 2, "Διάρκεια": 3, "Άνεση": 3}
