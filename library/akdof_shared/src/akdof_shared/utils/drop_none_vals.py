def drop_none_vals(dictionary: dict):
    """Non-recursively drop any key, value pair where value is None"""
    return {k: v for k,v in dictionary.items() if v is not None}