#!/usr/bin/env python3
"""
upload.py — Upload a produce image and detect all food items + freshness ratings.
             Plated meals are detected as a single unit, rated by their most
             perishable ingredient.

Usage:
    python upload.py path/to/image.jpg
    python upload.py path/to/image.png
    python upload.py path/to/image.jpg --json
    python upload.py path/to/image.jpg --date-purchased 2025-07-10
    python upload.py path/to/image.jpg -d 07/10/2025
"""

import sys
import json
import base64
import argparse
import math
from pathlib import Path
from datetime import datetime, timedelta
import boto3

# ── AWS clients ────────────────────────────────────────────────────────────────
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

# ── Freshness status labels ────────────────────────────────────────────────────
FRESHNESS_THRESHOLDS = [
    (0,  0,  'spoiled',    'critical'),
    (1,  2,  'use today',  'urgent'),
    (3,  5,  'use soon',   'warning'),
    (6,  14, 'fresh',      'good'),
    (15, 999,'very fresh', 'excellent'),
]

def freshness_status(days_remaining: int) -> dict:
    for low, high, label, urgency in FRESHNESS_THRESHOLDS:
        if low <= days_remaining <= high:
            return {'label': label, 'urgency': urgency}
    return {'label': 'unknown', 'urgency': 'unknown'}


def freshness_scale(days_remaining: int | None, typical_shelf_life: int | None) -> int | None:
    """
    Convert days_remaining into a 0–10 freshness scale.
    Uses the item's typical_shelf_life as the reference for 10/10.
    Falls back to a generic curve if typical_shelf_life is unknown.

      10 = just bought / peak fresh (>= 90% of shelf life remaining)
       0 = spoiled / should be discarded
    """
    if days_remaining is None:
        return None
    if days_remaining <= 0:
        return 0

    if typical_shelf_life and typical_shelf_life > 0:
        ratio = days_remaining / typical_shelf_life
        return min(10, max(0, round(ratio * 10)))

    return min(10, max(0, round(math.log(days_remaining + 1, 16) * 10)))


# ── Smart units ────────────────────────────────────────────────────────────────

WEIGHT_CATEGORIES = {'meat', 'dairy'}
WEIGHT_KEYWORDS   = {
    'steak', 'chicken', 'beef', 'pork', 'lamb', 'salmon', 'tuna', 'shrimp',
    'mince', 'ground', 'fillet', 'breast', 'thigh', 'wing', 'rib',
    'cheese', 'butter', 'yogurt', 'cream', 'milk',
    'flour', 'sugar', 'rice', 'pasta', 'oats',
}

CUT_KEYWORDS = {
    'cut', 'sliced', 'chopped', 'diced', 'shredded', 'grated',
    'cooked', 'leftover', 'soup', 'stew', 'salad', 'mixed',
}

def smart_unit(name: str, category: str) -> str:
    lower = name.lower()
    if category in WEIGHT_CATEGORIES:
        return 'weight'
    if any(kw in lower for kw in WEIGHT_KEYWORDS):
        return 'weight'
    if any(kw in lower for kw in CUT_KEYWORDS):
        return 'weight'
    return 'count'


# ── Per-unit gram lookup for countable items ───────────────────────────────────
COUNT_UNIT_GRAMS = {
    'large apple':    215, 'small apple':    150, 'apple':        182,
    'large banana':   136, 'small banana':    90, 'banana':       120,
    'large orange':   184, 'small orange':    96, 'orange':       130,
    'lemon':           58, 'lime':            67,
    'pear':           178, 'peach':          150, 'plum':          66,
    'mango':          200, 'kiwi':            76, 'avocado':      150,
    'grapefruit':     246, 'fig':             50, 'apricot':       35,
    'nectarine':      142, 'persimmon':      168,
    'cherry tomato':   17, 'roma tomato':     62, 'tomato':       123,
    'large potato':   300, 'small potato':   130, 'potato':       213,
    'sweet potato':   130,
    'large carrot':    72, 'carrot':          61,
    'large onion':    150, 'small onion':     70, 'onion':        110,
    'garlic head':     50, 'garlic clove':     4,
    'bell pepper':    119, 'cucumber':       201, 'zucchini':     196,
    'broccoli':       350, 'cauliflower':    588, 'cabbage':      908,
    'ear of corn':    103, 'corn':           103,
    'eggplant':       458, 'beet':           136, 'turnip':       122,
    'artichoke':      128, 'leek':           100,
    'large egg':       57, 'egg':             55,
    'slice of bread':  28, 'bagel':          105, 'dinner roll':   35,
    'croissant':       57, 'muffin':         113, 'tortilla':      45,
}

def gram_estimate_for_count(qty: int, name: str) -> int | None:
    lower = name.lower()
    for key in sorted(COUNT_UNIT_GRAMS, key=len, reverse=True):
        if key in lower:
            return qty * COUNT_UNIT_GRAMS[key]
    return None


def format_quantity(count: int | None, unit: str, name: str,
                    estimated_grams: int | None = None) -> str:
    if unit == 'count':
        qty = count if count and count > 0 else 1

        if estimated_grams and estimated_grams > 0:
            return f"{qty} (~{estimated_grams}g)"

        total_g = gram_estimate_for_count(qty, name)
        if total_g:
            return f"{qty} (~{total_g}g)"

        return str(qty)

    if estimated_grams and estimated_grams > 0:
        return f"~{estimated_grams}g"

    PER_UNIT_GRAMS = {
        'steak': 300, 'chicken breast': 200, 'chicken thigh': 150,
        'chicken wing': 90, 'salmon': 180, 'tuna': 170,
        'shrimp': 30, 'pork chop': 200, 'lamb chop': 180,
        'ground beef': 250, 'mince': 250, 'sausage': 100,
        'egg': 55, 'butter': 200, 'cheese': 200,
        'yogurt': 150, 'milk': 250,
    }
    qty = count if count and count > 0 else 1
    lower = name.lower()
    grams_each = next((v for k, v in PER_UNIT_GRAMS.items() if k in lower), None)
    if grams_each:
        return f"~{qty * grams_each}g"

    return "~?g (estimate unclear)"


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_image(path: str) -> tuple[bytes, str]:
    ext = Path(path).suffix.lower()
    media_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                 '.png': 'image/png',  '.webp': 'image/webp',
                 '.gif': 'image/gif'}
    media_type = media_map.get(ext, 'image/jpeg')
    with open(path, 'rb') as f:
        return f.read(), media_type


# ── Enrich a single raw item dict ─────────────────────────────────────────────

def enrich_item(item: dict, purchase_date: datetime) -> dict:
    """Add computed fields (status, scale, dates, quantity) to a raw AI item.

    The AI prompt now tells the model today's date and exactly how many days
    have elapsed since purchase, and instructs it to return days_remaining
    relative to TODAY — not the purchase date. So we no longer subtract elapsed
    time here; we trust the model's figure and compute expiration as
    today + days_remaining.
    """
    days_remaining = item.get('days_remaining')
    shelf_life     = item.get('typical_shelf_life')
    name           = item.get('name', '')
    category       = item.get('category', 'other')
    estimated_g    = item.get('estimated_grams')

    now = datetime.now()

    if days_remaining is not None:
        days_remaining = max(0, days_remaining)
        item['days_remaining'] = days_remaining
        status = freshness_status(days_remaining)
        item['freshness_status']  = status['label']
        item['freshness_urgency'] = status['urgency']
    else:
        item['freshness_status']  = 'unknown'
        item['freshness_urgency'] = 'unknown'

    item['freshness_scale'] = freshness_scale(days_remaining, shelf_life)
    item['date_added']      = purchase_date.strftime('%Y-%m-%d')

    if days_remaining is not None:
        # Expiration anchored to today since AI already baked in elapsed storage time
        expiry = now + timedelta(days=days_remaining)
        item['expiration_date'] = expiry.strftime('%Y-%m-%d')
    else:
        item['expiration_date'] = None

    unit = smart_unit(name, category)
    if estimated_g and estimated_g > 0:
        unit = 'weight'
    item['unit']     = unit
    item['quantity'] = format_quantity(
        item.get('count'), unit, name, estimated_grams=estimated_g
    )

    return item


# ── Bedrock: multi-item detection + freshness ─────────────────────────────────

def detect_all_items(image_bytes: bytes, media_type: str = 'image/jpeg',
                     purchase_date: datetime | None = None) -> list[dict]:
    if purchase_date is None:
        purchase_date = datetime.now()

    image_b64 = base64.b64encode(image_bytes).decode()

    today        = datetime.now().date()
    elapsed_days = (today - purchase_date.date()).days
    today_str    = today.strftime('%B %d, %Y')           # e.g. "April 18, 2026"
    bought_str   = purchase_date.strftime('%B %d, %Y')   # e.g. "March 28, 2026"

    if elapsed_days == 0:
        storage_context = (
            f"TODAY'S DATE: {today_str}\n"
            f"PURCHASE DATE: {bought_str} (purchased today — items are fresh from the store).\n"
            f"Use standard shelf-life values from date of purchase. Adjust only for any visible "
            f"deterioration already present in the image.\n"
            f"days_remaining should reflect how many days are left FROM TODAY."
        )
    else:
        elapsed_label = f"{elapsed_days} day{'s' if elapsed_days != 1 else ''}"
        storage_context = (
            f"TODAY'S DATE: {today_str}\n"
            f"PURCHASE DATE: {bought_str} ({elapsed_label} ago).\n"
            f"IMPORTANT: These items have already been stored for {elapsed_label}. "
            f"Factor this elapsed storage time directly into your days_remaining estimate — "
            f"it must reflect how many days are left FROM TODAY, not from the purchase date.\n"
            f"For example: if bananas typically last 7 days from purchase and {elapsed_label} "
            f"have passed, days_remaining should be approximately {max(0, 7 - elapsed_days)} "
            f"(adjusted further for any visible deterioration you can see in the image).\n"
            f"Use both the elapsed time AND visual cues together to give the most accurate "
            f"days_remaining value possible. If the item looks worse than expected for "
            f"{elapsed_label} of storage, lower your estimate accordingly."
        )

    prompt = f"""You are a food safety and produce expert. Look carefully at this image.

--- PURCHASE & STORAGE CONTEXT ---
{storage_context}
----------------------------------

STEP 1 — DECIDE: Is any food in the image a PLATED MEAL (i.e. multiple ingredients
combined and served together as a dish — e.g. pasta with sauce, a burger, a stir-fry,
a salad bowl, a pizza slice, a plate of food)? If so, treat that entire dish as ONE
meal item. DO NOT list its individual ingredients separately. Judge the freshness of
the meal by the ingredient that will go bad the soonest, and call out which ingredient
that is in freshness_notes.

Separate, unprepared, or packaged items that happen to be sitting near each other
(e.g. loose apples, raw vegetables, a bottle of sauce) are NOT a meal — list those
individually.

STEP 2 — For EVERY distinct item (or meal):

1. Name it specifically (e.g. "Spaghetti Bolognese", "Granny Smith Apple")
2. Categorize: fruit, vegetable, meat, dairy, bread, meal, drink, snack, condiment, dessert, or other
3. Confidence in the identification (0-100)
4. Count of visible units (integer; null if not meaningful for this item)
5. estimated_grams: required for meals, weight items, cut/portioned items, or loose bulk items.
   Null only for clearly whole countable items (e.g. 3 apples, 2 bananas).
6. Freshness assessment — using the purchase date and elapsed storage time above,
   combined with what you can see in the image:
   - days_remaining: integer — how many days are left FROM TODAY before the item should
     be discarded. Account for both elapsed storage time and any visible deterioration.
     For a MEAL, use the days_remaining of its LEAST fresh ingredient.
   - typical_shelf_life: integer — normal total shelf life from purchase for this item
     in good condition (used as a reference baseline, not the answer itself).
     For a MEAL, use the shelf life of the limiting ingredient.
   - limiting_ingredient: (meals only) name of the ingredient driving the freshness rating
   - freshness_notes: 1-2 sentences explaining your reasoning. Mention both the storage
     time elapsed and any visual cues that influenced your rating.

Visual freshness signals: color changes, texture, wilting, mold, bruising, dehydration.
If you cannot assess freshness, set days_remaining and typical_shelf_life to null.

Reply ONLY with a valid JSON array. No markdown, no extra text.
[
  {{
    "name": "Spaghetti Bolognese",
    "category": "meal",
    "confidence": 91,
    "count": 1,
    "estimated_grams": 480,
    "days_remaining": 1,
    "typical_shelf_life": 3,
    "limiting_ingredient": "ground beef",
    "freshness_notes": "Purchased {elapsed_days} day(s) ago; meat sauce shows slight darkening. Ground beef drives the rating — use today or tomorrow."
  }},
  {{
    "name": "Banana",
    "category": "fruit",
    "confidence": 97,
    "count": 3,
    "estimated_grams": null,
    "days_remaining": 0,
    "typical_shelf_life": 7,
    "limiting_ingredient": null,
    "freshness_notes": "Purchased {elapsed_days} day(s) ago; significant browning and dark spots confirm overripeness — should be used immediately or discarded."
  }}
]"""

    fmt = media_type.split("/")[1]
    if fmt == 'jpg':
        fmt = 'jpeg'

    try:
        response = bedrock.invoke_model(
            modelId='us.amazon.nova-pro-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "inferenceConfig": {"max_new_tokens": 1400},
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": fmt,
                                "source": {"bytes": image_b64}
                            }
                        },
                        {"text": prompt}
                    ]
                }]
            })
        )
        result = json.loads(response['body'].read())
        text   = result['output']['message']['content'][0]['text'].strip()

        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]

        parsed = json.loads(text)

        for item in parsed:
            item['source'] = 'bedrock'
            enrich_item(item, purchase_date)

        return parsed

    except Exception as e:
        print(f"[Bedrock] error: {e}", file=sys.stderr)
        return []


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

def freshness_bar(scale: int | None, width: int = 10) -> str:
    if scale is None:
        return '⚪' * width + '  (unknown)'
    filled = max(0, min(scale, width))
    bar    = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {scale}/10"

def print_results(items: list[dict], image_path: str,
                  purchase_date: datetime | None = None) -> None:
    if not items:
        print("\n  No food items detected.")
        return

    print(f"\n{'─'*60}")
    print(f"  Found {len(items)} item(s) in: {Path(image_path).name}")
    if purchase_date:
        today = datetime.now().date()
        elapsed = (today - purchase_date.date()).days
        if elapsed == 0:
            label = "purchased today"
        elif elapsed == 1:
            label = "purchased yesterday"
        else:
            label = f"purchased {elapsed} day(s) ago"
        print(f"  Date purchased : {purchase_date.strftime('%Y-%m-%d')}  ({label})")
    print(f"{'─'*60}")

    by_cat: dict[str, list] = {}
    for item in items:
        cat = item.get('category', 'other')
        by_cat.setdefault(cat, []).append(item)

    # Always show meals first
    ordered_cats = sorted(by_cat.keys(), key=lambda c: (0 if c == 'meal' else 1, c))

    for cat in ordered_cats:
        group = by_cat[cat]
        emoji = CATEGORY_EMOJI.get(cat, '•')
        print(f"\n  {emoji}  {cat.upper()}")
        for item in sorted(group, key=lambda x: x.get('days_remaining') or 999):
            conf        = item.get('confidence', '?')
            days        = item.get('days_remaining')
            urgency     = item.get('freshness_urgency', 'unknown')
            status      = item.get('freshness_status', 'unknown')
            symbol      = URGENCY_SYMBOL.get(urgency, '⚪')
            notes       = item.get('freshness_notes', '')
            limiting    = item.get('limiting_ingredient')
            days_str    = f"{days}d left" if days is not None else 'freshness unknown'
            scale       = item.get('freshness_scale')
            bar         = freshness_bar(scale)
            qty         = item.get('quantity', '?')
            added       = item.get('date_added', '?')
            expiry      = item.get('expiration_date', '?')

            print(f"\n     {symbol} {item['name']}  ({conf}% conf)")
            print(f"        Quantity   : {qty}")
            print(f"        Freshness  : {status.upper()} — {days_str}")
            print(f"        Scale      : {bar}")
            if limiting:
                print(f"        Limited by : {limiting}")
            print(f"        Purchased  : {added}")
            print(f"        Expires    : {expiry if expiry else 'unknown'}")
            if notes:
                print(f"        Visual cues: {notes}")

    print(f"\n{'─'*60}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_date(value: str) -> datetime:
    """Parse a date string in YYYY-MM-DD or MM/DD/YYYY format."""
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Invalid date '{value}'. Use YYYY-MM-DD or MM/DD/YYYY."
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description='Detect food items and freshness in an image.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('image', help='Path to the image file (jpg, png, webp)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output raw JSON instead of formatted text')
    parser.add_argument(
        '--date-purchased', '-d',
        metavar='DATE',
        type=parse_date,
        default=None,
        help=(
            'Date the items were purchased (default: today). '
            'Accepts YYYY-MM-DD or MM/DD/YYYY. '
            'Example: --date-purchased 2025-07-10'
        ),
    )
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

    purchase_date = args.date_purchased or datetime.now()

    # Warn if the purchase date is in the future
    if purchase_date.date() > datetime.now().date():
        print(
            f"  Warning: purchase date {purchase_date.strftime('%Y-%m-%d')} is in the future. "
            "Days-remaining will be inflated.", file=sys.stderr
        )

    print(f"\n  Loading image: {path}")
    image_bytes, media_type = load_image(str(path))
    print(f"    Size: {len(image_bytes):,} bytes  |  Type: {media_type}")
    print(f"  Purchase date : {purchase_date.strftime('%Y-%m-%d')}")
    print("  Running Bedrock (Nova Pro) detection...")

    items = detect_all_items(image_bytes, media_type, purchase_date=purchase_date)

    if args.json:
        print(json.dumps(items, indent=2))
    else:
        print_results(items, str(path), purchase_date=purchase_date)


if __name__ == '__main__':
    main()