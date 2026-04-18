#!/usr/bin/env python3
"""
upload.py — Upload a produce image and detect all food items + freshness ratings.

Usage:
    python upload.py path/to/image.jpg
    python upload.py path/to/image.png --verbose
    python upload.py path/to/image.jpg --json
"""

import sys
import json
import base64
import argparse
from pathlib import Path
import boto3

# ── AWS clients ────────────────────────────────────────────────────────────────
rekognition = boto3.client('rekognition', region_name='us-west-2')
bedrock     = boto3.client('bedrock-runtime', region_name='us-west-2')

# ── Constants ──────────────────────────────────────────────────────────────────
GENERIC_LABELS = {'food', 'food presentation', 'produce', 'ingredient', 'meal', 'dish', 'fruit', 'vegetable', 'meat', 'dairy', 'plant', 'flora'}

FOOD_KEYWORDS = [
    'food', 'fruit', 'vegetable', 'meat', 'dairy', 'bread', 'drink', 'meal',
    'snack', 'produce', 'ingredient', 'beverage', 'cheese', 'fish', 'dessert',
    'sauce', 'condiment', 'seafood', 'grain', 'herb', 'spice', 'egg', 'pasta'
]

CATEGORIES = {
    'fruit': [
        'apple', 'banana', 'fruit', 'berry', 'citrus', 'orange', 'grape',
        'strawberry', 'blueberry', 'raspberry', 'watermelon', 'mango',
        'pineapple', 'peach', 'pear', 'cherry', 'lemon', 'lime', 'kiwi',
        'coconut', 'fig', 'plum', 'melon', 'papaya'
    ],
    'vegetable': [
        'vegetable', 'broccoli', 'carrot', 'lettuce', 'spinach', 'kale',
        'tomato', 'potato', 'onion', 'garlic', 'pepper', 'cucumber',
        'celery', 'cabbage', 'mushroom', 'zucchini', 'eggplant', 'corn',
        'pea', 'bean', 'asparagus', 'cauliflower', 'radish', 'beet',
        'artichoke', 'leek', 'squash', 'pumpkin', 'yam', 'sweet potato', 'avocado'
    ],
    'meat': [
        'meat', 'chicken', 'beef', 'pork', 'fish', 'seafood', 'steak',
        'bacon', 'sausage', 'turkey', 'lamb', 'shrimp', 'salmon', 'tuna',
        'crab', 'lobster', 'duck', 'ham', 'salami', 'pepperoni', 'brisket',
        'ribs', 'wings', 'fillet', 'meatball', 'ground beef', 'veal'
    ],
    'dairy': [
        'dairy', 'cheese', 'milk', 'yogurt', 'butter', 'cream', 'egg',
        'mozzarella', 'cheddar', 'parmesan', 'brie', 'feta', 'gouda',
        'ricotta', 'whipped cream', 'ice cream', 'custard', 'cottage cheese'
    ],
    'bread': [
        'bread', 'bakery', 'pastry', 'grain', 'toast', 'bagel', 'muffin',
        'croissant', 'roll', 'bun', 'pita', 'tortilla', 'waffle', 'pancake',
        'biscuit', 'pretzel', 'cracker', 'sourdough', 'focaccia',
        'naan', 'flatbread', 'cornbread', 'brioche'
    ],
    'meal': [
        'pizza', 'pasta', 'burger', 'sandwich', 'salad', 'soup', 'stew',
        'curry', 'sushi', 'taco', 'burrito', 'bowl', 'rice', 'noodle',
        'ramen', 'stir fry', 'casserole', 'lasagna', 'quiche', 'omelette',
        'fried rice', 'paella', 'risotto', 'dumpling', 'spring roll',
        'avocado toast', 'wrap', 'poke', 'bibimbap', 'pad thai',
        'falafel', 'shawarma', 'gyro', 'hot dog', 'quesadilla', 'nachos'
    ],
    'drink': [
        'drink', 'beverage', 'juice', 'soda', 'coffee', 'tea', 'smoothie',
        'milkshake', 'lemonade', 'water', 'beer', 'wine', 'cocktail',
        'espresso', 'latte', 'cappuccino', 'matcha', 'kombucha'
    ],
    'snack': [
        'snack', 'chip', 'candy', 'chocolate', 'cookie', 'popcorn', 'nuts',
        'granola', 'bar', 'pretzel', 'dip', 'hummus', 'trail mix', 'jerky',
        'rice cake', 'energy bar'
    ],
    'condiment': [
        'sauce', 'ketchup', 'mustard', 'mayo', 'dressing', 'vinegar',
        'oil', 'salsa', 'guacamole', 'jam', 'honey', 'syrup',
        'soy sauce', 'hot sauce', 'relish', 'pesto', 'tahini'
    ],
    'dessert': [
        'cake', 'pie', 'dessert', 'sweet', 'donut', 'brownie', 'pudding',
        'tart', 'cheesecake', 'macaron', 'cupcake', 'gelato', 'sorbet',
        'tiramisu', 'mousse', 'crepe', 'churro', 'baklava', 'cookie'
    ]
}

# ── Freshness status labels ────────────────────────────────────────────────────
FRESHNESS_THRESHOLDS = [
    (0,  0,  'spoiled',    'critical'),
    (1,  2,  'use today',  'urgent'),
    (3,  5,  'use soon',   'warning'),
    (6,  14, 'fresh',      'good'),
    (15, 999,'very fresh', 'excellent'),
]

def freshness_status(days_remaining: int) -> dict:
    """Return a status label and urgency level for a given days_remaining value."""
    for low, high, label, urgency in FRESHNESS_THRESHOLDS:
        if low <= days_remaining <= high:
            return {'label': label, 'urgency': urgency}
    return {'label': 'unknown', 'urgency': 'unknown'}


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_category(label_name: str, parents: list[str]) -> str:
    all_names = [label_name.lower()] + [p.lower() for p in parents]
    priority = ['meal', 'dessert', 'drink', 'snack', 'condiment',
                'meat', 'dairy', 'bread', 'vegetable', 'fruit']
    ordered = priority + [k for k in CATEGORIES if k not in priority]
    for category in ordered:
        if any(k in n for n in all_names for k in CATEGORIES[category]):
            return category
    return 'other'


def is_food_label(label: dict) -> bool:
    name    = label['Name'].lower()
    parents = [p['Name'].lower() for p in label.get('Parents', [])]
    return any(k in name for k in FOOD_KEYWORDS) or \
           any(k in p    for p in parents for k in FOOD_KEYWORDS)


def load_image(path: str) -> tuple[bytes, str]:
    """Read image bytes and detect media type."""
    ext = Path(path).suffix.lower()
    media_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                 '.png': 'image/png',  '.webp': 'image/webp',
                 '.gif': 'image/gif'}
    media_type = media_map.get(ext, 'image/jpeg')
    with open(path, 'rb') as f:
        return f.read(), media_type


# ── Rekognition: extract all distinct food labels ─────────────────────────────

def rekognition_multi_detect(image_bytes: bytes) -> list[dict]:
    """
    Return a list of distinct food items found by Rekognition.
    Each item: {name, category, confidence, source}
    Note: Rekognition cannot assess freshness — that is handled by Bedrock.
    """
    try:
        response = rekognition.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=30,
            MinConfidence=70
        )
    except Exception as e:
        print(f"[Rekognition] error: {e}", file=sys.stderr)
        return []

    labels = response['Labels']
    food_labels = [l for l in labels if is_food_label(l)]
    specific    = [l for l in food_labels if l['Name'].lower() not in GENERIC_LABELS]

    items = []
    seen  = set()

    for label in specific:
        name    = label['Name']
        parents = [p['Name'] for p in label.get('Parents', [])]
        cat     = get_category(name, parents)

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        items.append({
            'name':       name,
            'category':   cat,
            'confidence': round(label['Confidence'], 1),
            'source':     'rekognition',
        })

    return items


# ── Bedrock: comprehensive multi-item detection + freshness ───────────────────

def bedrock_multi_detect(image_bytes: bytes, media_type: str = 'image/jpeg') -> list[dict]:
    """
    Send the image to Nova Pro via Bedrock and ask it to:
      - List every distinct food/produce item visible
      - Assess the freshness/spoilage of each item from visual cues

    Returns list of dicts, each containing:
      name, category, confidence, count,
      days_remaining, freshness_notes, source
    """
    image_b64 = base64.b64encode(image_bytes).decode()

    prompt = """You are a food safety and produce expert who can assess both what food items are present in an image AND estimate their freshness/spoilage from visual cues.

Look carefully at this image. For EVERY distinct food or produce item you can see:

1. Identify the item (specific name, e.g. "Granny Smith Apple", "Roma Tomato")
2. Categorize it: fruit, vegetable, meat, dairy, bread, meal, drink, snack, condiment, dessert, or other
3. Estimate how confident you are in the identification (0-100)
4. Count how many of this item are visible (integer, 1 if unsure)
5. Assess freshness from VISUAL CUES ONLY:
   - days_remaining: integer estimate of how many days the item has left before spoiling (0 = already spoiled/should discard, use realistic shelf-life knowledge)
   - freshness_notes: 1-2 sentences describing what visual cues you used (e.g. "slight yellowing at edges", "wilting leaves", "brown spots on skin", "vibrant color and firm appearance", "mold visible on surface")

Visual freshness signals to look for:
- Color changes (yellowing, browning, darkening)
- Texture changes (wilting, shriveling, soft spots, wrinkling)
- Surface defects (mold, cuts, bruising, discoloration)
- Structural integrity (drooping leaves, collapsed shape)
- Signs of dehydration or over-ripeness

If you cannot see the item clearly enough to assess freshness, set days_remaining to null and freshness_notes to "unable to assess from image".

Reply ONLY with a valid JSON array. No markdown, no explanation, no extra text.
Format:
[
  {
    "name": "Banana",
    "category": "fruit",
    "confidence": 97,
    "count": 3,
    "days_remaining": 2,
    "freshness_notes": "Skin shows significant browning and dark spots indicating overripeness"
  },
  {
    "name": "Broccoli",
    "category": "vegetable",
    "confidence": 92,
    "count": 1,
    "days_remaining": 5,
    "freshness_notes": "Florets appear deep green and compact with no yellowing visible"
  }
]"""

    try:
        response = bedrock.invoke_model(
            modelId='us.amazon.nova-pro-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": media_type.split("/")[1],
                                "source": {
                                    "bytes": image_b64,
                                }
                            }
                        },
                        {"text": prompt}
                    ]
                }]
            })
        )
        result = json.loads(response['body'].read())
        text   = result['output']['message']['content'][0]['text'].strip()

        # strip accidental markdown fences
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]

        parsed = json.loads(text)

        # Enrich each item with derived freshness status
        for item in parsed:
            item['source'] = 'bedrock'
            days = item.get('days_remaining')
            if days is not None:
                status = freshness_status(days)
                item['freshness_status'] = status['label']
                item['freshness_urgency'] = status['urgency']
            else:
                item['freshness_status'] = 'unknown'
                item['freshness_urgency'] = 'unknown'

        return parsed

    except Exception as e:
        print(f"[Bedrock] error: {e}", file=sys.stderr)
        return []


# ── Main detection: merge both sources ───────────────────────────────────────

def detect_all_items(image_bytes: bytes, media_type: str = 'image/jpeg',
                     verbose: bool = False) -> list[dict]:
    """
    Hybrid detection:
    1. Run Rekognition for fast, high-confidence item labels.
    2. Always also run Bedrock for comprehensive multi-item detection + freshness.
    3. Merge results — Bedrock wins on conflicts (and always provides freshness).
       Rekognition items that Bedrock missed are added without freshness data.
    """

    print("  Running Rekognition label detection...")
    rek_items = rekognition_multi_detect(image_bytes)
    if verbose and rek_items:
        print(f"    Rekognition found: {[i['name'] for i in rek_items]}")

    print("  Running Bedrock (Nova Pro) multi-item + freshness analysis...")
    bed_items = bedrock_multi_detect(image_bytes, media_type)
    if verbose and bed_items:
        print(f"    Bedrock found: {[i['name'] for i in bed_items]}")

    # Bedrock is authoritative; its items (with freshness) take precedence
    merged = {item['name'].lower(): item for item in bed_items}

    for rek in rek_items:
        key = rek['name'].lower()
        if not any(key in k or k in key for k in merged):
            rek.setdefault('days_remaining',    None)
            rek.setdefault('freshness_notes',   'Freshness assessment requires Bedrock analysis')
            rek.setdefault('freshness_status',  'unknown')
            rek.setdefault('freshness_urgency', 'unknown')
            merged[key] = rek

    return list(merged.values())


# ── Output formatting ─────────────────────────────────────────────────────────

CATEGORY_EMOJI = {
    'fruit':      '🍎',
    'vegetable':  '🥦',
    'meat':       '🥩',
    'dairy':      '🧀',
    'bread':      '🍞',
    'meal':       '🍽️',
    'drink':      '🥤',
    'snack':      '🍿',
    'condiment':  '🫙',
    'dessert':    '🍰',
    'other':      '🔍',
}

URGENCY_SYMBOL = {
    'critical':  '🔴',
    'urgent':    '🟠',
    'warning':   '🟡',
    'good':      '🟢',
    'excellent': '🟢',
    'unknown':   '⚪',
}

def print_results(items: list[dict], image_path: str) -> None:
    if not items:
        print("\n  No food items detected.")
        return

    print(f"\n{'─'*60}")
    print(f"  Found {len(items)} item(s) in: {Path(image_path).name}")
    print(f"{'─'*60}")

    by_cat: dict[str, list] = {}
    for item in items:
        cat = item.get('category', 'other')
        by_cat.setdefault(cat, []).append(item)

    for cat, group in sorted(by_cat.items()):
        emoji = CATEGORY_EMOJI.get(cat, '•')
        print(f"\n  {emoji}  {cat.upper()}")
        for item in sorted(group, key=lambda x: x.get('days_remaining') or 999):
            count   = item.get('count', 1)
            conf    = item.get('confidence', '?')
            src     = item.get('source', '')
            badge   = f"[{src}]" if src else ''
            qty     = f"x{count}" if count and count > 1 else ''
            days    = item.get('days_remaining')
            urgency = item.get('freshness_urgency', 'unknown')
            status  = item.get('freshness_status', 'unknown')
            symbol  = URGENCY_SYMBOL.get(urgency, '⚪')
            notes   = item.get('freshness_notes', '')

            days_str = f"{days}d left" if days is not None else 'freshness unknown'

            print(f"\n     {symbol} {item['name']} {qty}  ({conf}% conf) {badge}")
            print(f"        Freshness: {status.upper()} — {days_str}")
            if notes and notes != 'Freshness assessment requires Bedrock analysis':
                print(f"        Visual cues: {notes}")

    print(f"\n{'─'*60}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description='Detect food items and freshness in an image.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('image', help='Path to the image file (jpg, png, webp)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show intermediate detection results')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output raw JSON instead of formatted text')
    return parser.parse_args()


def main():
    args = parse_args()

    path = Path(args.image)
    if not path.exists():
        print(f"Error: file not found — {path}", file=sys.stderr)
        sys.exit(1)

    if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
        print(f"Error: unsupported file type '{path.suffix}'. "
              "Use jpg, png, webp, or gif.", file=sys.stderr)
        sys.exit(1)

    print(f"\n  Loading image: {path}")
    image_bytes, media_type = load_image(str(path))
    print(f"    Size: {len(image_bytes):,} bytes  |  Type: {media_type}")

    items = detect_all_items(image_bytes, media_type, verbose=args.verbose)

    if args.json:
        print(json.dumps(items, indent=2))
    else:
        print_results(items, str(path))


if __name__ == '__main__':
    main()