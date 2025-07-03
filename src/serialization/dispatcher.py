from functools import singledispatch

def serialize(obj, format: str = "json"):
    """
    Serialize an object to a specific format.

    Args:
        obj: The object to serialize.
        format: The format to serialize to (default is "json").

    Returns:
        The serialized object as a string.
    """

    if format == "json":
        return serialize(obj)

