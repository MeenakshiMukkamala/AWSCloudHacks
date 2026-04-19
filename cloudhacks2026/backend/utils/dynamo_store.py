# dynamo_store.py
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('FreshnessTracker')

def save_item(user_id: str, item: dict):
    from datetime import date
    
    # Image scans don't have date_purchased — use today
    date_purchased = item.get('date_purchased') or str(date.today())
    
    record = {
        'user_id':            user_id,
        'item_key':           f"{item['name']}#{date_purchased}",
        'name':               item['name'],
        'category':           item.get('category', 'other'),
        'date_purchased':     date_purchased,
        'typical_shelf_life': item['typical_shelf_life'],
        'quantity':           item.get('quantity', ''),
        'unit':               item.get('unit', 'count'),
        'storage_tip':        item.get('storage_tip', ''),
        'freshness_notes':    item.get('freshness_notes', ''),
        'confidence':         item.get('confidence', 0),
        'source':             item.get('source', 'bedrock'),
        'added_at':           datetime.now().isoformat(),
    }
    table.put_item(Item=record)
    print(f"  ✓ Saved to DynamoDB: {record['item_key']}")


def list_items(user_id: str) -> list[dict]:
    """Fetch all items and recompute freshness from today's date."""
    from boto3.dynamodb.conditions import Key
    from datetime import date

    resp  = table.query(KeyConditionExpression=Key('user_id').eq(user_id))
    today = date.today()
    items = []

    for r in resp['Items']:
        purchased     = datetime.strptime(r['date_purchased'], '%Y-%m-%d').date()
        days_elapsed  = (today - purchased).days
        days_remaining = max(0, int(r['typical_shelf_life']) - days_elapsed)

        # Re-use your existing helpers
        from upload import freshness_status, freshness_scale, freshness_bar
        status = freshness_status(days_remaining)

        items.append({
            **r,
            'days_remaining':   days_remaining,
            'freshness_status': status['label'],
            'freshness_urgency': status['urgency'],
            'freshness_scale':  freshness_scale(days_remaining, int(r['typical_shelf_life'])),
        })

    return sorted(items, key=lambda x: x['days_remaining'])
