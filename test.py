#!/usr/bin/env python3

import numpy as np
import pandas as pd
import logging
import logging.config
from algorithms.utastar import *

logging.config.fileConfig("logging.conf")

multicrit_tbl = pd.read_csv("tests/public_transport.csv", index_col=0)
crit_monot = {"Τιμή": False, "Διάρκεια": False, "Άνεση": True}
a_split = {"Τιμή": 2, "Διάρκεια": 3, "Άνεση": 3}

a = utastar(multicrit_tbl, crit_monot, a_split, 0.05, 0.01)

logging.info("Hello!")
