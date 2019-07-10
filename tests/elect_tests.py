from time import sleep
import os
import unittest
import json
from app import app, elect
from app import UPLOAD_DIR
from models import create_tables, get_database, Bite, Apple, STATUS_COMPLETE, STATUS_NEW

database = get_database()

sleep_time = 1  # in seconds


class ElectTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        create_tables()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # creates a test client
        self.app = app.test_client()
        # propagate the exceptions to the test client
        self.app.testing = True
        app.testing = True

    def tearDown(self):
        pass

    def test_pages_status_code(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)

        result = self.app.get('/list_bites')
        self.assertEqual(result.status_code, 200)

        result = self.app.get('/list')
        self.assertEqual(result.status_code, 200)

    def test_add_bite(self):
        table_name = "volleyball_single"
        table_col = 0
        data = {'table': table_name, 'col_id': table_col, 'slice': 0, 'total': 1}
        Bite.delete().execute()  # delete all Bites
        Apple.delete().execute()  # delete all Apples
        result = self.app.post('/add', data=data, content_type='multipart/form-data')
        self.assertIn('apple', result.json)
        apple_id = result.json['apple']
        self.assertEqual(result.status_code, 200, msg=result.data)
        database.connect(reuse_if_open=True)
        self.assertEqual(len(Bite.select()), 1)
        sleep(sleep_time)
        result = self.app.get('/status')
        self.assertEqual(result.status_code, 200, msg=result.data)
        self.assertTrue(result.is_json)
        j = {
            "apples": [
                {
                    "apple": table_name,
                    "status": STATUS_COMPLETE,
                    "complete": True,
                    "agreement": 1.0,
                    "elected": 0,
                }
            ]
        }
        self.assertEqual(elect(apple_id), None)  # just for the coverage

    def test_add_multiple_bite(self):
        table_name = "volleyball_double"
        table_col = 0
        data = {'table': table_name, 'col_id': table_col, 'slice': 0, 'total': 2}
        Bite.delete().execute()  # delete all Bites
        Apple.delete().execute()  # delete all Apples
        result = self.app.post('/add', data=data, content_type='multipart/form-data')
        self.assertEqual(result.status_code, 200, msg=result.data)
        database.connect(reuse_if_open=True)
        self.assertEqual(len(Bite.select()), 1)
        sleep(sleep_time)
        result = self.app.get('/status')
        self.assertEqual(result.status_code, 200, msg=result.data)
        self.assertTrue(result.is_json)
        j = {
            "apples": [
                {
                    "apple": table_name,
                    "status": STATUS_NEW,
                    "complete": False,
                    "elected": None,
                    "agreement": None,
                }
            ]
        }
        self.assertDictEqual(result.get_json(), j)
        data = {'table': table_name, 'col_id': table_col, 'slice': 1, 'total': 2}
        result = self.app.post('/add', data=data, content_type='multipart/form-data')
        self.assertEqual(result.status_code, 200, msg=result.data)
        database.connect(reuse_if_open=True)
        self.assertEqual(len(Bite.select()), 2)
        sleep(sleep_time)
        result = self.app.get('/status')
        self.assertEqual(result.status_code, 200, msg=result.data)
        self.assertTrue(result.is_json)
        j = {
            "apples": [
                {
                    "apple": table_name,
                    "status": STATUS_COMPLETE,
                    "complete": True,
                    "agreement": 1.0,
                    "elected": table_col,
                }
            ]
        }
