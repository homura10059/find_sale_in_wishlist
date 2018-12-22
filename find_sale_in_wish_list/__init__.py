from boto3.dynamodb.types import TypeDeserializer

VERSION = '0.4.0'

deserializer = TypeDeserializer()


def deserialize(image):
    """
    dictに変換する
    """
    d = {}
    for key in image:
        d[key] = deserializer.deserialize(image[key])
    return d