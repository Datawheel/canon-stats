# -*- coding: utf-8 -*-
import sys
import numpy as np
import pandas as pd
from .relatedness import relatedness

def opportunity_gain(rcas, proximities, pci):
    rcas = rcas.copy()
    rcas[rcas >= 1] = 1
    rcas[rcas < 1] = 0

    # turn proximities in to ratios out of total
    prox_ratio = proximities / proximities.sum()

    # get the inverse of the RCAs matrix. Since they are in the form of 1's and
    # 0's this will flip all of them i.e. 1 = 0 and 0 = 1
    inverse_rcas = 1 - rcas
    
    # convert PCIs to a matrix of repeated values
    pci_matrix = pd.DataFrame(pci.values.reshape((1, len(pci))), columns=pci.index)
    pci_matrix = pci_matrix.reindex(index=rcas.columns, method="ffill") # forward fill

    # here we now have the middle part of the equation
    middle = inverse_rcas.dot(pci_matrix)

    # get the relatedness with the backwards bizzaro RCAs
    dcp = relatedness(1-rcas, proximities)
    # now get the inverse
    dcp = 1-dcp
    # we now have the right-half of the equation
    right = dcp.dot(pci_matrix)

    # matrix multiplication with proximities ratio
    opp_gain = middle.dot(prox_ratio) - right

    return opp_gain