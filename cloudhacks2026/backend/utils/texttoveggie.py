#!/usr/bin/env python3
"""
texttoveggie.py — Look up freshness for a food item by name, date, and quantity.
                    Uses AWS Bedrock (Nova Pro) to reason about the item.

Usage:
    python text_vegetable.py "broccoli" "2026-04-15" --qty 2
    python text_vegetable.py "chicken breast" "2026-04-17" -q 500 --json
"""

import sys
import json
import argparse
import math
from datetime import datetime, timedelta
import boto3

# ── AWS client ─────────────────────────────────────────────────────────────────
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

# ── Freshness status labels ────────────────────────────────────────────────────
FRESHNESS_THRESHOLDS = [
    (0,   0,  'spoiled',    'critical'),
    (1,   2,  'use today',  'urgent'),
    (3,   5,  'use soon',   'warning'),
    (6,  14,  'fresh',      'good'),
    (15, 999, 'very fresh', 'excellent'),
]

def freshness_status(days_remaining: int) -> dict:
    for low, high, label, urgency in FRESHNESS_THRESHOLDS:
        if low <= days_remaining <= high:
            return {'label': label, 'urgency': urgency}
    return {'label': 'unknown', 'urgency': 'unknown'}


def freshness_scale(days_remaining: int, typical_shelf_life: int) -> int:
    """0-10 scale."""
    if days_remaining <= 0:
        return 0
    if typical_shelf_life > 0:
        return min(10, max(0, round(days_remaining / typical_shelf_life * 10)))
    return min(10, max(0, round(math.log(days_remaining + 1, 16) * 10)))


# ── Smart units ────────────────────────────────────────────────────────────────
WEIGHT_CATEGORIES = {'meat', 'dairy'}
WEIGHT_KEYWORDS = {
    'steak', 'chicken', 'beef', 'pork', 'lamb', 'salmon', 'tuna', 'shrimp',
    'mince', 'ground', 'fillet', 'breast', 'thigh', 'wing', 'rib',
    'cheese', 'butter', 'yogurt', 'cream', 'milk', 'flour', 'sugar', 
    'rice', 'pasta', 'oats', 'kimchi', 'sauce', 'soup', 'stew'
}
CUT_KEYWORDS = {'cut', 'sliced', 'chopped', 'diced', 'shredded', 'grated', 'cooked', 'leftover'}

def smart_unit(name: str, category: str) -> str:
    lo = name.lower()
    if category in WEIGHT_CATEGORIES:           return 'weight'
    if any(kw in lo for kw in WEIGHT_KEYWORDS): return 'weight'
    if any(kw in lo for kw in CUT_KEYWORDS):    return 'weight'
    return 'count'


# ── Gram lookups ───────────────────────────────────────────────────────────────
COUNT_UNIT_GRAMS = {
    'apple': 182, 'banana': 120, 'orange': 130, 'lemon': 58, 'lime': 67,
    'pear': 178, 'peach': 150, 'plum': 66, 'mango': 200, 'kiwi': 76, 
    'avocado': 150, 'tomato': 123, 'potato': 213, 'carrot': 61,
    'onion': 110, 'garlic head': 50, 'bell pepper': 119, 'broccoli': 350,
    'egg': 55, 'slice of bread': 28, 'bagel': 105,
}

def format_quantity(count: int | None, unit: str, name: str,
                    estimated_grams: int | None = None) -> str:
    qty = count if count and count > 0 else 1
    lo  = name.lower()
    
    if unit == 'count':
        # Try to find a gram match for the unit
        tg = next((v for k, v in COUNT_UNIT_GRAMS.items() if k in lo), None)
        if estimated_grams and estimated_grams > 0:
            return f"{qty} (~{estimated_grams}g)"
        if tg:
            return f"{qty} (~{qty * tg}g)"
        return str(qty)
    
    # Weight handling
    if estimated_grams and estimated_grams > 0:
        return f"~{estimated_grams}g"
    
    # Fallback default weight if none provided but unit is weight
    return f"~{qty * 150}g (est.)"


# ── Bedrock: text-only freshness reasoning ─────────────────────────────────────

def query_bedrock(name: str, date_purchased: datetime, user_qty: str = None) -> dict:
    days_since = (datetime.now() - date_purchased).days
    today_str  = datetime.now().strftime('%Y-%m-%d')
    bought_str = date_purchased.strftime('%Y-%m-%d')
    
    qty_context = f"The user has {user_qty} of this item." if user_qty else ""

    prompt = f"""You are a food safety expert. A user purchased "{name}" on {bought_str}. {qty_context}
Today is {today_str}, so it has been {days_since} day(s) since purchase.

Using standard food safety knowledge, return a JSON object. No null values.

Fields:
- name (string): Proper name
- category (string): fruit, vegetable, meat, dairy, bread, drink, snack, condiment, dessert, other
- confidence (integer 0-100)
- count (integer): Whole-unit count (default 1)
- estimated_grams (integer): Grams if weight-based, else 0.
- typical_shelf_life (integer): Standard days from purchase.
- days_remaining (integer): typical_shelf_life minus {days_since}. Min 0.
- storage_tip (string): One sentence.
- freshness_notes (string): 2 sentences explaining current state and spoilage signs.

Reply ONLY with valid JSON."""

    response = bedrock.invoke_model(
        modelId='us.amazon.nova-pro-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            "inferenceConfig": {"max_new_tokens": 600},
            "messages": [{
                "role": "user",
                "content": [{"text": prompt}]
            }]
        })
    )

    result = json.loads(response['body'].read())
    text   = result['output']['message']['content'][0]['text'].strip()

    if '```' in text:
        text = text.split('```')[1].replace('json', '').strip()

    return json.loads(text)


# ── Enrich item with computed fields ──────────────────────────────────────────

def enrich_item(item: dict, date_purchased: datetime, user_qty: str = None) -> dict:
    now = datetime.now()
    name = item.get('name', '')
    category = item.get('category', 'other')
    
    # Handle user-provided quantity override
    if user_qty:
        # Extract digits from strings like "500g" or "3 items"
        clean_val = "".join(filter(str.isdigit, user_qty))
        val = int(clean_val) if clean_val else 1
        
        # Decide if the input is a count or weight based on keywords and value magnitude
        is_likely_weight = val > 40 or any(k in name.lower() for k in WEIGHT_KEYWORDS)
        
        if is_likely_weight:
            item['estimated_grams'] = val
            item['count'] = 1
        else:
            item['count'] = val
            item['estimated_grams'] = 0

    days = max(0, item.get('days_remaining', 0))
    shelf_life = max(1, item.get('typical_shelf_life', 7))
    eg = item.get('estimated_grams')

    item['days_remaining'] = days
    item['typical_shelf_life'] = shelf_life

    status = freshness_status(days)
    item['freshness_status']  = status['label']
    item['freshness_urgency'] = status['urgency']
    item['freshness_scale']   = freshness_scale(days, shelf_life)
    item['date_purchased']    = date_purchased.strftime('%Y-%m-%d')
    item['expiration_date']   = (date_purchased + timedelta(days=shelf_life)).strftime('%Y-%m-%d')
    
    unit = smart_unit(name, category)
    if eg and eg > 0:
        unit = 'weight'
    
    item['unit'] = unit
    item['quantity'] = format_quantity(item.get('count'), unit, name, eg)

    return item


# ── Output formatting ─────────────────────────────────────────────────────────

CATEGORY_EMOJI = {
    'fruit': '🍎', 'vegetable': '🥦', 'meat': '🥩', 'dairy': '🧀',
    'bread': '🍞', 'meal': '🍽️',  'drink': '🥤', 'snack': '🍿',
    'condiment': '🫙', 'dessert': '🍰', 'other': '🔍',
}

URGENCY_SYMBOL = {
    'critical': '🔴', 'urgent': '🟠', 'warning': '🟡',
    'good': '🟢', 'excellent': '🟢', 'unknown': '⚪',
}

def freshness_bar(scale: int, width: int = 10) -> str:
    filled = max(0, min(scale, width))
    return f"[{'█' * filled}{'░' * (width - filled)}] {scale}/10"

def print_result(item: dict) -> None:
    cat    = item.get('category', 'other')
    emoji  = CATEGORY_EMOJI.get(cat, '•')
    symbol = URGENCY_SYMBOL.get(item.get('freshness_urgency', 'unknown'), '⚪')
    
    print(f"\n{'─'*60}")
    print(f"  {emoji}  {item['name'].upper()}  —  {cat.upper()}")
    print(f"{'─'*60}")
    print(f"  {symbol} Freshness    : {item['freshness_status'].upper()} — {item['days_remaining']}d remaining")
    print(f"     Scale       : {freshness_bar(item['freshness_scale'])}")
    print(f"     Quantity    : {item['quantity']}")
    print(f"     Purchased   : {item['date_purchased']}")
    print(f"     Expires     : {item['expiration_date']}")
    print(f"     Shelf life  : {item['typical_shelf_life']} days from purchase")
    print(f"     Confidence  : {item.get('confidence', '?')}%")
    if item.get('storage_tip'):
        print(f"\n  Storage tip  : {item['storage_tip']}")
    if item.get('freshness_notes'):
        print(f"  Notes        : {item['freshness_notes']}")
    print(f"\n{'─'*60}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Food Freshness Lookup')
    parser.add_argument('name', help='Food name')
    parser.add_argument('date_purchased', help='YYYY-MM-DD')
    parser.add_argument('--qty', '-q', help='Quantity (e.g. "3" or "500")')
    parser.add_argument('--json', '-j', action='store_true', help='Output JSON')
    args = parser.parse_args()

    try:
        date_purchased = datetime.strptime(args.date_purchased, '%Y-%m-%d')
        if date_purchased > datetime.now():
            print("Error: Purchase date is in the future.", file=sys.stderr)
            sys.exit(1)
            
        days_since = (datetime.now() - date_purchased).days
        print(f"\n  Item      : {args.name!r}")
        print(f"  Purchased : {args.date_purchased}  ({days_since} day(s) ago)")
        print("  Querying Bedrock (Nova Pro)...")

        raw = query_bedrock(args.name, date_purchased, args.qty)
        item = enrich_item(raw, date_purchased, args.qty)

        if args.json:
            print(json.dumps(item, indent=2))
        else:
            print_result(item)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
