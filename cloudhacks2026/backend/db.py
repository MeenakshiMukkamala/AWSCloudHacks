import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ingredients')

def add_ingredient(item, user_id="demo"):
    item_id = str(uuid.uuid4())

    record = {
        "id": item_id,
        "user_id": user_id,
        "name": item["name"],
        "buy_date": item.get("buy_date"),
        "created_at": datetime.utcnow().isoformat()
    }

    table.put_item(Item=record)
    return record


def get_all(user_id="demo"):
    res = table.scan()
    return res.get("Items", [])