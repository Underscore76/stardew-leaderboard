import boto3

from leaderboard_api.config import dynamodb_table_name, get_settings


def get_table():
    name = dynamodb_table_name()
    dynamodb = boto3.resource("dynamodb", region_name=get_settings().aws_region)
    return dynamodb.Table(name)

