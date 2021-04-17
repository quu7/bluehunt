#!/usr/bin/env python3

import numpy as np
#import scipy as sp
import pandas as pd
from utastar import *


multicrit_tbl = pd.read_csv('public_transport.csv')
crit_monot = [False, False, True]
a_split = np.array([2, 3, 3])

crit_values = multicrit_tbl.iloc[:,2:]
