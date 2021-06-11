# -*- coding: utf-8 -*-
import sys
import numpy as np
import pandas as pd
from .relatedness import relatedness

def relative_relatedness(rcas,proximities):
    opportunity = rcas.copy()
    opportunity[opportunity >= 1] = np.nan
    opportunity[opportunity < 1] = 1
    wcp = relatedness(rcas,proximities)
    wcp_opp = opportunity*wcp
    wcp_mean =  wcp_opp.mean(axis=1)
    wcp_std =  wcp_opp.std(axis=1)

    return wcp.transform(lambda x: (x-wcp_mean)/wcp_std)
    