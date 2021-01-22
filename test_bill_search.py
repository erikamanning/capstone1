from unittest import TestCase
from app import app, db
from flask import session
from models import User, PolicyArea

from bill_test_utility_functions import add_dummy_bill, remove_dummy_bills, remove_dummy_policy_areas
from datetime import date 
  
app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['WTF_CSRF_ENABLED'] = False

TODAY = date.today()

class TestBillSearch(TestCase):

    @classmethod
    def setUpClass(cls):

        # add dummy bills
        cls.policy_area_str_1 = 'dummy Cartoon Dog Regulations'
        cls.policy_area_str_2 = 'dummy Anti Rainwater Laws'

        add_dummy_bill('a',cls.policy_area_str_1,TODAY, TODAY)
        add_dummy_bill('b',cls.policy_area_str_2 ,'2021-01-04', '2021-01-04')
        add_dummy_bill('c',cls.policy_area_str_2 ,'2021-01-05', '2021-01-05')

        cls.policy_area_1 = PolicyArea.query.filter(PolicyArea.name==cls.policy_area_str_1).one_or_none()
        cls.policy_area_2 = PolicyArea.query.filter(PolicyArea.name==cls.policy_area_str_2).one_or_none()

        print('Setup')
    

    @classmethod
    def tearDownClass(cls):

        remove_dummy_bills()
        remove_dummy_policy_areas()
        print("Teardown")

    # test if correct bills load with no data passed to form
    def test_bill_search_any_subject(self):
        with app.test_client() as client:
            d= {
                'policy_area' : '',
                'start_date' : '',
                'end_date' : ''
            }
            resp = client.get('/bills', data=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_a', html)

    # test if correct bills load with a specific subject passed to form
    def test_bill_search_specific_subject_a(self):
        with app.test_client() as client:
            d= {
                'policy_area' : TestBillSearch.policy_area_1.id,
                'start_date' : '',
                'end_date' : ''
            }
            resp = client.get(f'/bills',query_string=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_a', html)
            self.assertNotIn('dummy_bill_b', html)

    #test if correct bills load with a specific subject passed to form
    def test_bill_search_specific_subject_b(self):
        with app.test_client() as client:
            d= {
                'policy_area' : TestBillSearch.policy_area_2.id,
                'start_date' : '',
                'end_date' : ''
            }
            resp = client.get(f'/bills',query_string=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_b', html)
            self.assertIn('dummy_bill_c', html)
            self.assertNotIn('dummy_bill_a', html)

    #test if correct bills load with a specific subject & date passed to form
    def test_bill_search_specific_subject_date(self):
        with app.test_client() as client:
            d= {
                'policy_area' : TestBillSearch.policy_area_2.id,
                'start_date' : '2021-01-04',
                'end_date' : '2021-01-04'
            }
            resp = client.get(f'/bills',query_string=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_b', html)
            self.assertNotIn('dummy_bill_c', html)

    #test if correct bills load with start date only passed to form
    def test_bill_search_only_start_date(self):
        with app.test_client() as client:
            d= {
                'policy_area' : '',
                'start_date' : TODAY,
                'end_date' : ''
            }
            resp = client.get(f'/bills',query_string=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_a', html)
            self.assertNotIn('dummy_bill_b', html)
            self.assertNotIn('dummy_bill_c', html)

    #test if correct bills load with end date only passed to form
    def test_bill_search_only_end_date(self):
        with app.test_client() as client:
            d= {
                'policy_area' : '',
                'start_date' : '',
                'end_date' : TODAY
            }
            resp = client.get(f'/bills',query_string=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_a', html)
            self.assertNotIn('dummy_bill_b', html)
            self.assertNotIn('dummy_bill_c', html)

    #test if correct bills load with start & end date only passed to form
    def test_bill_search_only_full_date(self):
        with app.test_client() as client:
            d= {
                'policy_area' : '',
                'start_date' : TODAY,
                'end_date' : TODAY
            }
            resp = client.get(f'/bills',query_string=d)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('dummy_bill_a', html)
            self.assertNotIn('dummy_bill_b', html)
            self.assertNotIn('dummy_bill_c', html)


