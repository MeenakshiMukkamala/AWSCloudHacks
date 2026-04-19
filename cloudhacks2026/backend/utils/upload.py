#!/usr/bin/env python3
"""
upload.py — Upload a produce image and detect all food items + freshness ratings.
             Plated meals are detected as a single unit, rated by their most
             perishable ingredient.

Usage:
    python upload.py path/to/image.jpg
    python upload.py path/to/image.png
    python upload.py path/to/image.jpg --json
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


def freshness_scale(days_remaining: int | None, typical_shelf_life: int | None) -> int:
    """
    Convert days_remaining into a 0–10 freshness scale.
    Uses the item's typical_shelf_life as the reference for 10/10.
    Falls back to a logarithmic curve if typical_shelf_life is unknown.
    Always returns an integer (never None).

      10 = just bought / peak fresh (>= 100% of shelf life remaining)
       0 = spoiled / should be discarded
    """
    if days_remaining is None or days_remaining <= 0:
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

    CATEGORY_GRAM_DEFAULTS = {
        'meat': 250, 'dairy': 200, 'vegetable': 150,
        'fruit': 150, 'bread': 80, 'meal': 400,
        'snack': 50, 'condiment': 200, 'other': 100,
    }
    fallback_g = CATEGORY_GRAM_DEFAULTS.get(
        next((k for k in CATEGORY_GRAM_DEFAULTS if k in lower), ''), 150
    )
    return f"~{qty * fallback_g}g (est.)"


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_image(path: str) -> tuple[bytes, str]:
    ext = Path(path).suffix.lower()
    media_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                 '.png': 'image/png',  '.webp': 'image/webp',
                 '.gif': 'image/gif'}
    media_type = media_map.get(ext, 'image/jpeg')
    with open(path, 'rb') as f:
        return f.read(), media_type


# ── Category-based fallback shelf lives (days) ────────────────────────────────

CATEGORY_SHELF_LIFE_DEFAULTS = {
    'fruit':     10,
    'vegetable': 10,
    'meat':       3,
    'dairy':      7,
    'bread':      5,
    'meal':       3,
    'drink':     14,
    'snack':     60,
    'condiment': 90,
    'dessert':    4,
    'other':      7,
}

NAME_SHELF_LIFE_DEFAULTS = {
    'potato': 30, 'sweet potato': 21, 'yam': 21,
    'carrot': 21, 'onion': 60, 'garlic': 120, 'shallot': 30,
    'apple': 14, 'pear': 10, 'orange': 14, 'grapefruit': 21,
    'lemon': 21, 'lime': 21, 'banana': 7, 'grape': 7,
    'strawberry': 5, 'blueberry': 7, 'raspberry': 3,
    'mango': 7, 'pineapple': 5, 'melon': 7, 'watermelon': 7,
    'peach': 5, 'plum': 5, 'cherry': 7, 'kiwi': 10,
    'avocado': 5, 'fig': 3, 'apricot': 5,
    'tomato': 7, 'cucumber': 7, 'zucchini': 7, 'bell pepper': 10,
    'broccoli': 7, 'cauliflower': 7, 'cabbage': 21,
    'lettuce': 7, 'spinach': 5, 'kale': 7, 'celery': 14,
    'mushroom': 7, 'corn': 3, 'asparagus': 4, 'green bean': 7,
    'beet': 14, 'turnip': 14, 'parsnip': 14, 'leek': 10,
    'eggplant': 7, 'artichoke': 7, 'brussel sprout': 7,
    'kimchi': 14, 'sauerkraut': 30,
    'raw chicken': 2, 'raw beef': 3, 'raw pork': 3, 'raw fish': 2,
    'cooked chicken': 4, 'cooked beef': 4,
    'milk': 7, 'yogurt': 14, 'hard cheese': 30, 'soft cheese': 7,
    'egg': 35, 'butter': 30,
    'bread': 7, 'bagel': 5, 'croissant': 2, 'tortilla': 7,
}

def get_shelf_life_default(name: str, category: str) -> int:
    lower = name.lower()
    for key in sorted(NAME_SHELF_LIFE_DEFAULTS, key=len, reverse=True):
        if key in lower:
            return NAME_SHELF_LIFE_DEFAULTS[key]
    return CATEGORY_SHELF_LIFE_DEFAULTS.get(category, 7)


def apply_freshness_fallbacks(item: dict) -> dict:
    name     = item.get('name', '')
    category = item.get('category', 'other')

    shelf_life = item.get('typical_shelf_life')
    if not isinstance(shelf_life, int) or shelf_life <= 0:
        shelf_life = get_shelf_life_default(name, category)
        item['typical_shelf_life'] = shelf_life

    days = item.get('days_remaining')
    if not isinstance(days, int):
        item['days_remaining'] = shelf_life
        existing_notes = item.get('freshness_notes') or ''
        if existing_notes:
            item['freshness_notes'] = (
                existing_notes.rstrip('.')
                + f' No spoilage cues detected; estimated at full shelf life ({shelf_life} days).'
            )
        else:
            item['freshness_notes'] = (
                f'No visible spoilage detected. Freshness estimated at full '
                f'shelf life for this item ({shelf_life} days).'
            )

    if item.get('count') is None:
        unit_hint = smart_unit(name, category)
        if unit_hint == 'count':
            item['count'] = 1

    if item.get('estimated_grams') is None:
        unit_hint = smart_unit(name, category)
        cnt = item.get('count') or 1
        if unit_hint == 'weight':
            derived = gram_estimate_for_count(cnt, name)
            if derived:
                item['estimated_grams'] = derived
            else:
                item.pop('estimated_grams', None)
        else:
            item.pop('estimated_grams', None)

    if category != 'meal':
        item.pop('limiting_ingredient', None)
    elif item.get('limiting_ingredient') is None:
        item['limiting_ingredient'] = 'unknown ingredient'

    if not item.get('freshness_notes'):
        item['freshness_notes'] = (
            f'No visible spoilage or quality issues detected for this {category}.'
        )

    return item


# ── Enrich a single raw item dict ─────────────────────────────────────────────

def enrich_item(item: dict, now: datetime) -> dict:
    item = apply_freshness_fallbacks(item)

    days        = item.get('days_remaining')
    shelf_life  = item.get('typical_shelf_life')
    name        = item.get('name', '')
    category    = item.get('category', 'other')
    estimated_g = item.get('estimated_grams')

    status = freshness_status(days)
    item['freshness_status']  = status['label']
    item['freshness_urgency'] = status['urgency']

    item['freshness_scale'] = freshness_scale(days, shelf_life)
    item['date_added']      = now.strftime('%Y-%m-%d %H:%M')

    expiry = now + timedelta(days=days)
    item['expiration_date'] = expiry.strftime('%Y-%m-%d')

    unit = smart_unit(name, category)
    if estimated_g and estimated_g > 0:
        unit = 'weight'
    item['unit']     = unit
    item['quantity'] = format_quantity(
        item.get('count'), unit, name, estimated_grams=estimated_g
    )

    return item


# ── Bedrock: multi-item detection + freshness ─────────────────────────────────

def detect_all_items(image_bytes: bytes, media_type: str = 'image/jpeg') -> list[dict]:
    image_b64 = base64.b64encode(image_bytes).decode()

    prompt = """You are a food safety and produce expert. Your ONLY job is to report exactly what you see in this image. Do NOT rely on assumptions, prior knowledge of typical states, or expectations about how a food usually looks. Every judgment must be grounded in specific, visible pixels in this image.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE RULES — read before doing anything else
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. DESCRIBE ONLY WHAT IS VISIBLE. If a banana is green, say it is green. If skin is smooth, say so. Never project a "typical" appearance onto what you see.
2. NEVER use generic or template language. Every freshness_notes field must describe THIS specific item in THIS image — color, texture, surface condition as they actually appear.
3. DO NOT invent spoilage that is not visible. Do not mention browning, spots, or wilting unless you can clearly see them.
4. DO NOT deny freshness that IS visible. If an item looks crisp, firm, bright — say so and score accordingly.
5. days_remaining and typical_shelf_life must ALWAYS be integers. NEVER null.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — MEAL vs INDIVIDUAL ITEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Is food in this image a PLATED MEAL (multiple ingredients combined and served together — pasta, burger, stir-fry, salad bowl, pizza, plate of food)?
  → YES: treat the entire dish as ONE item, category "meal". Rate freshness by the most perishable ingredient visible. Name the limiting ingredient in limiting_ingredient.
  → NO: list each food item separately.

Loose, unprepared, or packaged items sitting near each other are NOT a meal — list individually.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — FOR EACH ITEM, REPORT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. name — specific (e.g. "Granny Smith Apple", not just "Apple")
2. category — fruit | vegetable | meat | dairy | bread | meal | drink | snack | condiment | dessert | other
3. confidence — 0–100, your confidence in the identification
4. count — integer count of visible whole units; null if not applicable
5. estimated_grams — required for meals, portioned/cut items, loose bulk. Null for clearly whole countable items (e.g. 3 whole apples).
6. Freshness fields — all based on what you can SEE right now:

   days_remaining (integer, NEVER null):
     Derive this ENTIRELY from visible evidence:
     - What COLOR is the skin/flesh? (green, yellow, yellow-green, brown patches, black spots?)
     - What is the TEXTURE? (firm, soft, wrinkled, shriveled, slimy?)
     - Are there visible DEFECTS? (mold, bruises, cuts, dehydration, slime?)
     Map your visual observations to days using this scale:
       Mold/slime/collapsing = 0
       Heavily wrinkled/very soft/strong discoloration = 1–2
       Some spots/soft patches/yellowing = 3–5
       Minor marks, slightly past peak = 6–9
       Firm, bright color, no defects, peak condition = use typical_shelf_life
     For green (unripe) items: add extra days — green bananas = 5–7+ days, unripe avocados = 4–6 days.

   typical_shelf_life (integer, NEVER null):
     The standard maximum shelf life for this item type at room temp or refrigerated (whichever is normal for it):
       potato: 30 | sweet potato: 21 | carrot: 21 | onion: 60 | garlic: 120
       apple: 14  | banana: 7        | orange: 14 | grape: 7  | strawberry: 5
       tomato: 7  | lettuce: 7       | spinach: 5 | broccoli: 7 | cucumber: 7
       bell pepper: 10 | zucchini: 7 | mushroom: 7 | celery: 14
       raw chicken: 2  | raw beef: 3 | raw fish: 2 | cooked leftovers: 4
       egg: 35 | milk: 7 | yogurt: 14 | hard cheese: 30 | butter: 30 | bread: 7

   limiting_ingredient — meals only, the ingredient driving the freshness rating; null otherwise

   freshness_notes — 2–3 sentences. MANDATORY CONTENT:
     • Sentence 1: Describe the ACTUAL COLOR and TEXTURE you see right now.
     • Sentence 2: List any visible defects (or explicitly state none are visible).
     • Sentence 3: Explain how those observations led to your days_remaining estimate.
     No generic statements. No assumptions. Only describe what is in this image.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reply ONLY with a valid JSON array. No markdown, no extra text.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[
  {
    "name": "Banana",
    "category": "fruit",
    "confidence": 97,
    "count": 3,
    "estimated_grams": null,
    "days_remaining": 6,
    "typical_shelf_life": 7,
    "limiting_ingredient": null,
    "freshness_notes": "Skin is uniformly yellow-green with no brown spots or dark patches visible. Surface appears smooth and firm with no wrinkling or soft areas. The green tinge indicates the bananas are not yet fully ripe, adding 1–2 days beyond a fully yellow banana."
  },
  {
    "name": "Russet Potato",
    "category": "vegetable",
    "confidence": 95,
    "count": 3,
    "estimated_grams": null,
    "days_remaining": 28,
    "typical_shelf_life": 30,
    "limiting_ingredient": null,
    "freshness_notes": "Skin is dry and light brown with a slightly rough texture typical of fresh russets. No green patches, soft spots, sprouting eyes, or surface damage are visible. Item appears freshly harvested or recently purchased with full shelf life remaining."
  }
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
        now    = datetime.now()

        for item in parsed:
            item['source'] = 'bedrock'
            enrich_item(item, now)

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

    ordered_cats = sorted(by_cat.keys(), key=lambda c: (0 if c == 'meal' else 1, c))

    for cat in ordered_cats:
        group = by_cat[cat]
        emoji = CATEGORY_EMOJI.get(cat, '•')
        print(f"\n  {emoji}  {cat.upper()}")
        for item in sorted(group, key=lambda x: x.get('days_remaining') or 999):
            conf     = item.get('confidence', '?')
            days     = item.get('days_remaining')
            urgency  = item.get('freshness_urgency', 'unknown')
            status   = item.get('freshness_status', 'unknown')
            symbol   = URGENCY_SYMBOL.get(urgency, '⚪')
            notes    = item.get('freshness_notes', '')
            limiting = item.get('limiting_ingredient')
            days_str = f"{days}d left" if days is not None else 'freshness unknown'
            scale    = item.get('freshness_scale')
            bar      = freshness_bar(scale)
            qty      = item.get('quantity', '?')
            added    = item.get('date_added', '?')
            expiry   = item.get('expiration_date', '?')

            print(f"\n     {symbol} {item['name']}  ({conf}% conf)")
            print(f"        Quantity   : {qty}")
            print(f"        Freshness  : {status.upper()} — {days_str}")
            print(f"        Scale      : {bar}")
            if limiting:
                print(f"        Limited by : {limiting}")
            print(f"        Date added : {added}")
            print(f"        Expires    : {expiry if expiry else 'unknown'}")
            if notes:
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
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output raw JSON instead of formatted text')
    parser.add_argument('--user', '-u', default='default',
                        help='User ID to associate with saved items (default: "default")')
    parser.add_argument('--no-save', action='store_true',
                        help='Skip saving to DynamoDB')
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
    print("  Running Bedrock (Nova Pro) detection...")

    items = detect_all_items(image_bytes, media_type)

    # ── Save to DynamoDB ───────────────────────────────────────────────────────
    if not args.no_save and items:
        try:
            from dynamo_store import save_item
            for item in items:
                save_item(user_id=args.user, item=item)
        except Exception as e:
            print(f"  [DynamoDB] Warning: could not save — {e}", file=sys.stderr)

    if args.json:
        print(json.dumps(items, indent=2))
    else:
        print_results(items, str(path))


# ── Lambda handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    """
    Expected request body (JSON):
        {
            "image":      "<base64-encoded image bytes>",
            "media_type": "image/jpeg",   (optional, default: image/jpeg)
            "user_id":    "aditya"        (optional, default: "default")
        }

    Returns:
        200 + list of enriched item dicts on success
        400 if image field is missing
        500 on any other error
    """
    try:
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)

        if 'image' not in body:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing required field: image (base64)'})
            }

        image_bytes = base64.b64decode(body['image'])
        media_type  = body.get('media_type', 'image/jpeg')
        user_id     = body.get('user_id', 'default')

        items = detect_all_items(image_bytes, media_type)

        # Save each detected item to DynamoDB
        try:
            from dynamo_store import save_item
            for item in items:
                save_item(user_id=user_id, item=item)
        except Exception as e:
            print(f"[DynamoDB] Warning: could not save — {e}")

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(items)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }


if __name__ == '__main__':
    main()
