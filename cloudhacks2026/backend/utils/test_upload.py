#!/usr/bin/env python3
"""
test_upload.py — Tests for upload.py (backend/utils/upload.py)

Run all tests:
    python test_upload.py

Run with verbose output:
    python test_upload.py -v

Run a single test:
    python test_upload.py TestFreshnessStatus.test_spoiled
"""

import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend' / 'utils'))
import upload  # noqa: E402


# ── Shared fake data ───────────────────────────────────────────────────────────

def make_rek_label(name, confidence=95.0, parents=None):
    return {
        'Name': name,
        'Confidence': confidence,
        'Parents': [{'Name': p} for p in (parents or [])],
    }

def make_rek_response(*labels):
    return {'Labels': list(labels)}

def make_bedrock_response(items: list):
    body_text = json.dumps(items)
    mock_body  = MagicMock()
    mock_body.read.return_value = json.dumps({
        'content': [{'type': 'text', 'text': body_text}]
    }).encode()
    return {'body': mock_body}


# ── Helpers ────────────────────────────────────────────────────────────────────

class TestGetCategory(unittest.TestCase):

    def test_fruit(self):
        self.assertEqual(upload.get_category('Apple', ['Fruit']), 'fruit')

    def test_vegetable(self):
        self.assertEqual(upload.get_category('Broccoli', ['Vegetable']), 'vegetable')

    def test_meat(self):
        self.assertEqual(upload.get_category('Chicken', ['Meat']), 'meat')

    def test_dairy(self):
        self.assertEqual(upload.get_category('Cheddar', ['Cheese', 'Dairy']), 'dairy')

    def test_unknown_returns_other(self):
        self.assertEqual(upload.get_category('Cardboard', []), 'other')

    def test_case_insensitive(self):
        self.assertEqual(upload.get_category('BANANA', []), 'fruit')


class TestIsFoodLabel(unittest.TestCase):

    def test_food_name(self):
        label = make_rek_label('Apple', parents=['Fruit', 'Food'])
        self.assertTrue(upload.is_food_label(label))

    def test_non_food(self):
        label = make_rek_label('Car', parents=['Vehicle'])
        self.assertFalse(upload.is_food_label(label))

    def test_food_in_parent_only(self):
        label = make_rek_label('Produce', parents=['Food'])
        self.assertTrue(upload.is_food_label(label))


class TestLoadImage(unittest.TestCase):

    def test_jpg_media_type(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff' + b'\x00' * 10)
            tmp = f.name
        try:
            data, mt = upload.load_image(tmp)
            self.assertEqual(mt, 'image/jpeg')
            self.assertIsInstance(data, bytes)
        finally:
            os.unlink(tmp)

    def test_png_media_type(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG' + b'\x00' * 10)
            tmp = f.name
        try:
            _, mt = upload.load_image(tmp)
            self.assertEqual(mt, 'image/png')
        finally:
            os.unlink(tmp)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            upload.load_image('/nonexistent/path/image.jpg')


# ── NEW: Freshness helpers ─────────────────────────────────────────────────────

class TestFreshnessStatus(unittest.TestCase):

    def test_spoiled(self):
        result = upload.freshness_status(0)
        self.assertEqual(result['label'], 'spoiled')
        self.assertEqual(result['urgency'], 'critical')

    def test_use_today(self):
        result = upload.freshness_status(1)
        self.assertEqual(result['label'], 'use today')
        self.assertEqual(result['urgency'], 'urgent')

    def test_use_today_boundary(self):
        result = upload.freshness_status(2)
        self.assertEqual(result['label'], 'use today')

    def test_use_soon(self):
        result = upload.freshness_status(4)
        self.assertEqual(result['label'], 'use soon')
        self.assertEqual(result['urgency'], 'warning')

    def test_fresh(self):
        result = upload.freshness_status(7)
        self.assertEqual(result['label'], 'fresh')
        self.assertEqual(result['urgency'], 'good')

    def test_very_fresh(self):
        result = upload.freshness_status(20)
        self.assertEqual(result['label'], 'very fresh')
        self.assertEqual(result['urgency'], 'excellent')

    def test_boundary_use_soon_to_fresh(self):
        self.assertEqual(upload.freshness_status(5)['label'], 'use soon')
        self.assertEqual(upload.freshness_status(6)['label'], 'fresh')

    def test_boundary_fresh_to_very_fresh(self):
        self.assertEqual(upload.freshness_status(14)['label'], 'fresh')
        self.assertEqual(upload.freshness_status(15)['label'], 'very fresh')


# ── Rekognition layer ──────────────────────────────────────────────────────────

class TestRekognitionMultiDetect(unittest.TestCase):

    @patch('upload.rekognition')
    def test_returns_multiple_items(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Apple',    95.5, ['Fruit', 'Food']),
            make_rek_label('Broccoli', 91.0, ['Vegetable', 'Food']),
            make_rek_label('Lemon',    88.0, ['Fruit', 'Food']),
        )
        items = upload.rekognition_multi_detect(b'fake_image_bytes')
        names = [i['name'] for i in items]
        self.assertIn('Apple',    names)
        self.assertIn('Broccoli', names)
        self.assertIn('Lemon',    names)

    @patch('upload.rekognition')
    def test_generic_labels_filtered_out(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Food',    99.0, []),
            make_rek_label('Produce', 98.0, ['Food']),
            make_rek_label('Banana',  95.0, ['Fruit', 'Food']),
        )
        items = upload.rekognition_multi_detect(b'fake_image_bytes')
        names = [i['name'].lower() for i in items]
        self.assertNotIn('food',    names)
        self.assertNotIn('produce', names)
        self.assertIn('banana',     names)

    @patch('upload.rekognition')
    def test_no_duplicates(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Apple', 97.0, ['Fruit', 'Food']),
            make_rek_label('Apple', 93.0, ['Fruit', 'Food']),
        )
        items = upload.rekognition_multi_detect(b'fake_image_bytes')
        apple_items = [i for i in items if i['name'] == 'Apple']
        self.assertEqual(len(apple_items), 1)

    @patch('upload.rekognition')
    def test_rekognition_error_returns_empty(self, mock_rek):
        mock_rek.detect_labels.side_effect = Exception('AWS connection error')
        items = upload.rekognition_multi_detect(b'fake_image_bytes')
        self.assertEqual(items, [])

    @patch('upload.rekognition')
    def test_non_food_labels_excluded(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Car',    99.0, ['Vehicle']),
            make_rek_label('Person', 98.0, []),
            make_rek_label('Mango',  91.0, ['Fruit', 'Food']),
        )
        items = upload.rekognition_multi_detect(b'fake_image_bytes')
        names = [i['name'].lower() for i in items]
        self.assertNotIn('car',    names)
        self.assertNotIn('person', names)
        self.assertIn('mango',     names)

    @patch('upload.rekognition')
    def test_rekognition_items_have_no_freshness(self, mock_rek):
        """Rekognition items should NOT have freshness data set (Bedrock fills that)."""
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Apple', 95.0, ['Fruit', 'Food']),
        )
        items = upload.rekognition_multi_detect(b'fake_image_bytes')
        self.assertEqual(len(items), 1)
        # days_remaining should not be set by Rekognition
        self.assertNotIn('days_remaining', items[0])


# ── Bedrock layer ──────────────────────────────────────────────────────────────

class TestBedrockMultiDetect(unittest.TestCase):

    @patch('upload.bedrock')
    def test_returns_all_items(self, mock_bed):
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Strawberry', 'category': 'fruit',     'confidence': 95, 'count': 6,
             'days_remaining': 3, 'freshness_notes': 'Bright red, firm'},
            {'name': 'Spinach',    'category': 'vegetable', 'confidence': 90, 'count': 1,
             'days_remaining': 1, 'freshness_notes': 'Wilting leaves visible'},
        ])
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['name'], 'Strawberry')
        self.assertEqual(items[1]['name'], 'Spinach')

    @patch('upload.bedrock')
    def test_source_tagged_as_bedrock(self, mock_bed):
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Peach', 'category': 'fruit', 'confidence': 88, 'count': 2,
             'days_remaining': 4, 'freshness_notes': 'Slight softening'},
        ])
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items[0]['source'], 'bedrock')

    @patch('upload.bedrock')
    def test_freshness_status_derived_correctly(self, mock_bed):
        """days_remaining=0 should yield freshness_status='spoiled'."""
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Banana', 'category': 'fruit', 'confidence': 91, 'count': 2,
             'days_remaining': 0, 'freshness_notes': 'Black skin, fully overripe'},
        ])
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items[0]['freshness_status'],  'spoiled')
        self.assertEqual(items[0]['freshness_urgency'], 'critical')

    @patch('upload.bedrock')
    def test_freshness_use_today(self, mock_bed):
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Spinach', 'category': 'vegetable', 'confidence': 89, 'count': 1,
             'days_remaining': 1, 'freshness_notes': 'Leaves wilting'},
        ])
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items[0]['freshness_status'], 'use today')

    @patch('upload.bedrock')
    def test_freshness_null_days_yields_unknown(self, mock_bed):
        """If Claude can't assess freshness (null), status should be 'unknown'."""
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Mystery Herb', 'category': 'other', 'confidence': 60, 'count': 1,
             'days_remaining': None, 'freshness_notes': 'Unable to assess from image'},
        ])
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items[0]['freshness_status'],  'unknown')
        self.assertEqual(items[0]['freshness_urgency'], 'unknown')

    @patch('upload.bedrock')
    def test_freshness_notes_preserved(self, mock_bed):
        notes = 'Deep green florets, no yellowing, firm stem'
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Broccoli', 'category': 'vegetable', 'confidence': 94, 'count': 1,
             'days_remaining': 7, 'freshness_notes': notes},
        ])
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items[0]['freshness_notes'], notes)

    @patch('upload.bedrock')
    def test_strips_markdown_fences(self, mock_bed):
        raw_items = [{'name': 'Tomato', 'category': 'vegetable', 'confidence': 92,
                      'count': 3, 'days_remaining': 5,
                      'freshness_notes': 'Firm, vibrant red skin'}]
        raw = f'```json\n{json.dumps(raw_items)}\n```'
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(
            {'content': [{'type': 'text', 'text': raw}]}
        ).encode()
        mock_bed.invoke_model.return_value = {'body': mock_body}
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items[0]['name'], 'Tomato')

    @patch('upload.bedrock')
    def test_bedrock_error_returns_empty(self, mock_bed):
        mock_bed.invoke_model.side_effect = Exception('Bedrock timeout')
        items = upload.bedrock_multi_detect(b'fake_image_bytes')
        self.assertEqual(items, [])


# ── Merge logic ────────────────────────────────────────────────────────────────

class TestDetectAllItems(unittest.TestCase):

    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_merges_both_sources(self, mock_rek, mock_bed):
        mock_rek.return_value = [
            {'name': 'Carrot', 'category': 'vegetable', 'confidence': 96, 'source': 'rekognition'},
        ]
        mock_bed.return_value = [
            {'name': 'Apple',  'category': 'fruit', 'confidence': 94, 'source': 'bedrock',
             'days_remaining': 5, 'freshness_status': 'use soon', 'freshness_urgency': 'warning'},
            {'name': 'Banana', 'category': 'fruit', 'confidence': 91, 'source': 'bedrock',
             'days_remaining': 1, 'freshness_status': 'use today', 'freshness_urgency': 'urgent'},
        ]
        items = upload.detect_all_items(b'fake')
        names = [i['name'] for i in items]
        self.assertIn('Apple',  names)
        self.assertIn('Banana', names)
        self.assertIn('Carrot', names)

    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_bedrock_wins_on_conflict(self, mock_rek, mock_bed):
        mock_rek.return_value = [
            {'name': 'Apple', 'category': 'other', 'confidence': 80, 'source': 'rekognition'},
        ]
        mock_bed.return_value = [
            {'name': 'Apple', 'category': 'fruit', 'confidence': 97, 'source': 'bedrock',
             'days_remaining': 6, 'freshness_status': 'fresh', 'freshness_urgency': 'good'},
        ]
        items = upload.detect_all_items(b'fake')
        apple = next(i for i in items if i['name'] == 'Apple')
        self.assertEqual(apple['source'],   'bedrock')
        self.assertEqual(apple['category'], 'fruit')
        self.assertEqual(apple['freshness_status'], 'fresh')

    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_rekognition_only_items_get_unknown_freshness(self, mock_rek, mock_bed):
        """Items found only by Rekognition should have freshness_status='unknown'."""
        mock_rek.return_value = [
            {'name': 'Papaya', 'category': 'fruit', 'confidence': 88, 'source': 'rekognition'},
        ]
        mock_bed.return_value = []   # Bedrock missed it
        items = upload.detect_all_items(b'fake')
        papaya = next(i for i in items if i['name'] == 'Papaya')
        self.assertEqual(papaya['freshness_status'],  'unknown')
        self.assertEqual(papaya['freshness_urgency'], 'unknown')
        self.assertIsNone(papaya['days_remaining'])

    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_handles_both_empty(self, mock_rek, mock_bed):
        mock_rek.return_value = []
        mock_bed.return_value = []
        items = upload.detect_all_items(b'fake')
        self.assertEqual(items, [])

    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_large_mixed_basket(self, mock_rek, mock_bed):
        mock_rek.return_value = [
            {'name': 'Lemon',    'category': 'fruit',     'confidence': 96, 'source': 'rekognition'},
            {'name': 'Broccoli', 'category': 'vegetable', 'confidence': 93, 'source': 'rekognition'},
        ]
        mock_bed.return_value = [
            {'name': 'Apple',    'category': 'fruit',     'confidence': 97, 'count': 3,
             'source': 'bedrock', 'days_remaining': 10, 'freshness_status': 'fresh',
             'freshness_urgency': 'good', 'freshness_notes': 'Firm, bright red'},
            {'name': 'Banana',   'category': 'fruit',     'confidence': 95, 'count': 2,
             'source': 'bedrock', 'days_remaining': 2,  'freshness_status': 'use today',
             'freshness_urgency': 'urgent', 'freshness_notes': 'Yellow with brown spots'},
            {'name': 'Tomato',   'category': 'vegetable', 'confidence': 92, 'count': 4,
             'source': 'bedrock', 'days_remaining': 4,  'freshness_status': 'use soon',
             'freshness_urgency': 'warning', 'freshness_notes': 'Slightly soft'},
            {'name': 'Broccoli', 'category': 'vegetable', 'confidence': 94, 'count': 1,
             'source': 'bedrock', 'days_remaining': 6,  'freshness_status': 'fresh',
             'freshness_urgency': 'good', 'freshness_notes': 'Dark green, compact'},
        ]
        items = upload.detect_all_items(b'fake')
        self.assertGreaterEqual(len(items), 4)
        # Broccoli should come from Bedrock (has freshness data)
        broccoli = next(i for i in items if i['name'] == 'Broccoli')
        self.assertEqual(broccoli['source'], 'bedrock')
        self.assertIsNotNone(broccoli.get('days_remaining'))


# ── print_results smoke tests ──────────────────────────────────────────────────

class TestPrintResults(unittest.TestCase):

    def test_empty_items(self):
        try:
            upload.print_results([], 'test.jpg')
        except Exception as e:
            self.fail(f"print_results raised unexpectedly: {e}")

    def test_multiple_categories_with_freshness(self):
        items = [
            {'name': 'Apple',   'category': 'fruit',     'confidence': 95, 'source': 'bedrock',
             'count': 2, 'days_remaining': 7,  'freshness_status': 'fresh',
             'freshness_urgency': 'good',     'freshness_notes': 'Crisp, bright red'},
            {'name': 'Spinach', 'category': 'vegetable', 'confidence': 91, 'source': 'bedrock',
             'count': 1, 'days_remaining': 1,  'freshness_status': 'use today',
             'freshness_urgency': 'urgent',   'freshness_notes': 'Leaves wilting badly'},
            {'name': 'Cheddar', 'category': 'dairy',     'confidence': 88, 'source': 'bedrock',
             'count': 1, 'days_remaining': 20, 'freshness_status': 'very fresh',
             'freshness_urgency': 'excellent','freshness_notes': 'No visible mold'},
        ]
        try:
            upload.print_results(items, 'basket.jpg')
        except Exception as e:
            self.fail(f"print_results raised unexpectedly: {e}")

    def test_spoiled_item_displayed(self):
        items = [
            {'name': 'Banana', 'category': 'fruit', 'confidence': 90, 'source': 'bedrock',
             'count': 1, 'days_remaining': 0, 'freshness_status': 'spoiled',
             'freshness_urgency': 'critical', 'freshness_notes': 'Fully black skin'},
        ]
        try:
            upload.print_results(items, 'old_fruit.jpg')
        except Exception as e:
            self.fail(f"print_results raised unexpectedly: {e}")

    def test_unknown_freshness_item(self):
        """Rekognition-only items with unknown freshness should display without crashing."""
        items = [
            {'name': 'Papaya', 'category': 'fruit', 'confidence': 85, 'source': 'rekognition',
             'days_remaining': None, 'freshness_status': 'unknown',
             'freshness_urgency': 'unknown',
             'freshness_notes': 'Freshness assessment requires Bedrock analysis'},
        ]
        try:
            upload.print_results(items, 'mystery.jpg')
        except Exception as e:
            self.fail(f"print_results raised unexpectedly: {e}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main(verbosity=2)