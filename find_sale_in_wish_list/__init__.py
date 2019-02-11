from boto3.dynamodb.types import TypeDeserializer
from decimal import Decimal

VERSION = '0.4.0'

deserializer = TypeDeserializer()


def deserialize(image: dict)-> dict:
    """
    dictに変換する
    """

    python_data = {}
    for key, val in image.items():
        if isinstance(val, dict):
            # dict は再帰的に変換する
            python_data[key] = deserialize(val)
        elif hasattr(val, "keys"):
            python_data[key] = deserializer.deserialize(val)
        else:
            python_data[key] = val
    return python_data


def decimal_default(obj: Decimal)-> float:
    """
    Decimal を float に返還するための function
    :param obj:
    :return:
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


