#!/usr/bin/env python3
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent / 'backend' / 'utils'))
import upload

def make_rek_label(name, confidence=95.0, parents=None):
    return {'Name': name, 'Confidence': confidence, 'Parents': [{'Name': p} for p in (parents or [])]}

def make_rek_response(*labels):
    return {'Labels': list(labels)}

def make_bedrock_response(items):
    body_text = json.dumps(items)
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps({'content': [{'type': 'text', 'text': body_text}]}).encode()
    return {'body': mock_body}

class TestGetCategory(unittest.TestCase):
    def test_fruit(self): self.assertEqual(upload.get_category('Apple', ['Fruit']), 'fruit')
    def test_vegetable(self): self.assertEqual(upload.get_category('Broccoli', ['Vegetable']), 'vegetable')
    def test_meat(self): self.assertEqual(upload.get_category('Chicken', ['Meat']), 'meat')
    def test_dairy(self): self.assertEqual(upload.get_category('Cheddar', ['Cheese', 'Dairy']), 'dairy')
    def test_unknown_returns_other(self): self.assertEqual(upload.get_category('Cardboard', []), 'other')
    def test_case_insensitive(self): self.assertEqual(upload.get_category('BANANA', []), 'fruit')
    def test_avocado_toast_is_meal(self): self.assertEqual(upload.get_category('Avocado Toast', ['Food']), 'meal')
    def test_avocado_alone_is_vegetable(self): self.assertEqual(upload.get_category('Avocado', ['Fruit', 'Food']), 'vegetable')

class TestIsFoodLabel(unittest.TestCase):
    def test_food_name(self): self.assertTrue(upload.is_food_label(make_rek_label('Apple', parents=['Fruit', 'Food'])))
    def test_non_food(self): self.assertFalse(upload.is_food_label(make_rek_label('Car', parents=['Vehicle'])))
    def test_food_in_parent_only(self): self.assertTrue(upload.is_food_label(make_rek_label('Produce', parents=['Food'])))

class TestLoadImage(unittest.TestCase):
    def test_jpg_media_type(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff' + b'\x00' * 10); tmp = f.name
        try:
            data, mt = upload.load_image(tmp)
            self.assertEqual(mt, 'image/jpeg')
        finally: os.unlink(tmp)
    def test_png_media_type(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'\x89PNG' + b'\x00' * 10); tmp = f.name
        try:
            _, mt = upload.load_image(tmp); self.assertEqual(mt, 'image/png')
        finally: os.unlink(tmp)
    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError): upload.load_image('/nonexistent/image.jpg')

class TestRekognitionMultiDetect(unittest.TestCase):
    @patch('upload.rekognition')
    def test_returns_multiple_items(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Apple', 95.5, ['Fruit', 'Food']),
            make_rek_label('Broccoli', 91.0, ['Vegetable', 'Food']),
            make_rek_label('Lemon', 88.0, ['Fruit', 'Food']))
        items = upload.rekognition_multi_detect(b'fake')
        names = [i['name'] for i in items]
        self.assertIn('Apple', names); self.assertIn('Broccoli', names); self.assertIn('Lemon', names)
    @patch('upload.rekognition')
    def test_generic_labels_filtered_out(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Food', 99.0), make_rek_label('Produce', 98.0, ['Food']),
            make_rek_label('Banana', 95.0, ['Fruit', 'Food']))
        items = upload.rekognition_multi_detect(b'fake')
        names = [i['name'].lower() for i in items]
        self.assertNotIn('food', names); self.assertNotIn('produce', names); self.assertIn('banana', names)
    @patch('upload.rekognition')
    def test_no_duplicates(self, mock_rek):
        mock_rek.detect_labels.return_value = make_rek_response(
            make_rek_label('Apple', 97.0, ['Fruit', 'Food']), make_rek_label('Apple', 93.0, ['Fruit', 'Food']))
        items = upload.rekognition_multi_detect(b'fake')
        self.assertEqual(len([i for i in items if i['name'] == 'Apple']), 1)
    @patch('upload.rekognition')
    def test_error_returns_empty(self, mock_rek):
        mock_rek.detect_labels.side_effect = Exception('AWS error')
        self.assertEqual(upload.rekognition_multi_detect(b'fake'), [])

class TestBedrockMultiDetect(unittest.TestCase):
    @patch('upload.bedrock')
    def test_returns_all_items(self, mock_bed):
        mock_bed.invoke_model.return_value = make_bedrock_response([
            {'name': 'Strawberry', 'category': 'fruit', 'confidence': 95, 'count': 6},
            {'name': 'Spinach', 'category': 'vegetable', 'confidence': 90, 'count': 1}])
        items = upload.bedrock_multi_detect(b'fake')
        self.assertEqual(len(items), 2); self.assertEqual(items[0]['name'], 'Strawberry')
    @patch('upload.bedrock')
    def test_source_tagged_as_bedrock(self, mock_bed):
        mock_bed.invoke_model.return_value = make_bedrock_response([{'name': 'Peach', 'category': 'fruit', 'confidence': 88, 'count': 2}])
        self.assertEqual(upload.bedrock_multi_detect(b'fake')[0]['source'], 'bedrock')
    @patch('upload.bedrock')
    def test_strips_markdown_fences(self, mock_bed):
        raw = '```json\n[{"name": "Tomato", "category": "vegetable", "confidence": 92, "count": 3}]\n```'
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({'content': [{'type': 'text', 'text': raw}]}).encode()
        mock_bed.invoke_model.return_value = {'body': mock_body}
        self.assertEqual(upload.bedrock_multi_detect(b'fake')[0]['name'], 'Tomato')
    @patch('upload.bedrock')
    def test_error_returns_empty(self, mock_bed):
        mock_bed.invoke_model.side_effect = Exception('Timeout')
        self.assertEqual(upload.bedrock_multi_detect(b'fake'), [])

class TestDetectAllItems(unittest.TestCase):
    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_merges_both_sources(self, mock_rek, mock_bed):
        mock_rek.return_value = [{'name': 'Carrot', 'category': 'vegetable', 'confidence': 96, 'source': 'rekognition'}]
        mock_bed.return_value = [{'name': 'Apple', 'category': 'fruit', 'confidence': 94, 'source': 'bedrock'},
                                  {'name': 'Banana', 'category': 'fruit', 'confidence': 91, 'source': 'bedrock'}]
        names = [i['name'] for i in upload.detect_all_items(b'fake')]
        self.assertIn('Apple', names); self.assertIn('Banana', names); self.assertIn('Carrot', names)
    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_bedrock_wins_on_conflict(self, mock_rek, mock_bed):
        mock_rek.return_value = [{'name': 'Apple', 'category': 'other', 'confidence': 80, 'source': 'rekognition'}]
        mock_bed.return_value = [{'name': 'Apple', 'category': 'fruit', 'confidence': 97, 'source': 'bedrock'}]
        items = upload.detect_all_items(b'fake')
        apple = next(i for i in items if i['name'] == 'Apple')
        self.assertEqual(apple['source'], 'bedrock'); self.assertEqual(apple['category'], 'fruit')
    @patch('upload.bedrock_multi_detect')
    @patch('upload.rekognition_multi_detect')
    def test_handles_both_empty(self, mock_rek, mock_bed):
        mock_rek.return_value = []; mock_bed.return_value = []
        self.assertEqual(upload.detect_all_items(b'fake'), [])

class TestPrintResults(unittest.TestCase):
    def test_empty_items(self):
        try: upload.print_results([], 'test.jpg')
        except Exception as e: self.fail(f"Raised: {e}")
    def test_multiple_categories(self):
        items = [{'name': 'Apple', 'category': 'fruit', 'confidence': 95, 'source': 'bedrock'},
                 {'name': 'Carrot', 'category': 'vegetable', 'confidence': 91, 'source': 'rekognition'}]
        try: upload.print_results(items, 'basket.jpg')
        except Exception as e: self.fail(f"Raised: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
