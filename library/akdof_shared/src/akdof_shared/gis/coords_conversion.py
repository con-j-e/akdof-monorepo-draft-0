def dd_to_ddm_lat(coord):
    """Converts decimal degrees latitude coordinate to degrees decimal minutes"""
    degree_sign = u'\N{DEGREE SIGN}'
    deg = abs(int(coord))
    min = (abs(coord) - deg) * 60
    if coord > 0:
        dir = "N"
    else:
        dir = "S"
    return "%s%s %s' %s"%(deg, degree_sign, "{:06.3f}".format(min), dir)

def dd_to_ddm_lng(coord):
    """Converts decimal degrees longitude coordinate to degrees decimal minutes"""
    degree_sign = u'\N{DEGREE SIGN}' 
    deg = abs(int(coord))
    min = (abs(coord) - deg) * 60
    if coord > 0:
        dir = "E"
    else:
        dir = "W"
    return "%s%s %s' %s"%(deg, degree_sign, "{:06.3f}".format(min), dir)
