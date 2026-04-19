# list_items.py
from dynamo_store import list_items
from upload import print_results  # reuse your formatter

items = list_items(user_id='aditya')
print_results(items, image_path='[from DynamoDB]')
