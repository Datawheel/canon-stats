from .density import density

def distance(rcas, proximities):
    return 1 - density(rcas, proximities)