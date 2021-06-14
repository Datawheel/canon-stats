# -*- coding: utf-8 -*-
import sys
import numpy as np
import pandas as pd
from .relatedness import relatedness

def relative_relatedness(rcas,proximities):
    wcp = relatedness(rcas,proximities)
    wcp_mean =  wcp.mean(axis=1)
    wcp_std =  wcp.std(axis=1)

    return wcp.transform(lambda x: (x-wcp_mean)/wcp_std)
    