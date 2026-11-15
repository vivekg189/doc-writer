"""
Comprehensive Automated Test Suite for Legal Entity Extraction & Rental Agreement Generation.
Covers:
1. Exact user benchmark sample.
2. Contextual role assignment (Landlord vs Tenant order independence).
3. Currency format variations (₹, Rs., INR, rupees, Lakhs, No. 25 address collision avoidance).
4. Duration and notice period duplication prevention ("11 months months", "30 days months'").
5. Validation guards (Landlord != Tenant, missing field placeholders).
6. Full Flask route integration test.
"""

import sys
import os
import unittest

# Ensure workspace root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, workspace_root)

from app.services.processor import LegalDocumentProcessor, number_to_words_indian, parse_indian_amount


class TestLegalEntityExtraction(unittest.TestCase):
    def setUp(self):
        self.processor = LegalDocumentProcessor()

    def test_number_to_words_indian(self):
        """Test Indian numbering system conversion."""
        self.assertEqual(number_to_words_indian(15000), "Fifteen Thousand")
        self.assertEqual(number_to_words_indian(50000), "Fifty Thousand")
        self.assertEqual(number_to_words_indian(150000), "One Lakh Fifty Thousand")
        self.assertEqual(number_to_words_indian(25000), "Twenty Five Thousand")
        self.assertEqual(number_to_words_indian("15,000"), "Fifteen Thousand")
        self.assertEqual(number_to_words_indian("50,000"), "Fifty Thousand")

    def test_parse_indian_amount(self):
        """Test currency parsing and lakh calculations."""
        clean_amt, words = parse_indian_amount("₹15,000")
        self.assertEqual(clean_amt, "15,000")
        self.assertEqual(words, "Fifteen Thousand")

        clean_amt, words = parse_indian_amount("Rs. 50,000")
        self.assertEqual(clean_amt, "50,000")
        self.assertEqual(words, "Fifty Thousand")

        clean_amt, words = parse_indian_amount("INR 15000")
        self.assertEqual(clean_amt, "15,000")

        clean_amt, words = parse_indian_amount("1.5 lakh rupees")
        self.assertEqual(clean_amt, "150,000")
        self.assertEqual(words, "One Lakh Fifty Thousand")

        clean_amt, words = parse_indian_amount("0.5 lakh")
        self.assertEqual(clean_amt, "50,000")
        self.assertEqual(words, "Fifty Thousand")

    def test_user_benchmark_sample(self):
        """Test the exact benchmark sample provided in the user prompt."""
        prompt = (
            "Create a rental agreement where Landlord is Rahul Sharma and Tenant is Arjun Kumar. "
            "The property is at No. 25, Anna Nagar, Chennai, Tamil Nadu. "
            "Monthly rent is ₹15,000 and security deposit is ₹50,000. "
            "Agreement duration is 11 months starting from 1 December 2026. "
            "Rent due date is 5th of every month and notice period is 30 days."
        )

        entities = self.processor.extract_entities(prompt)

        # 1. Parties
        self.assertEqual(entities['landlord'], 'Rahul Sharma')
        self.assertEqual(entities['tenant'], 'Arjun Kumar')
        self.assertNotEqual(entities['landlord'], entities['tenant'])

        # 2. Financials (Rent & Deposit)
        self.assertEqual(entities['rent_amount'], '15,000')
        self.assertEqual(entities['rent_amount_words'], 'Fifteen Thousand')
        self.assertEqual(entities['security_deposit'], '50,000')
        self.assertEqual(entities['security_deposit_words'], 'Fifty Thousand')
        # Crucial check: Address number '25' was NOT extracted as rent or deposit!
        self.assertNotEqual(entities['rent_amount'], '25')
        self.assertNotEqual(entities['security_deposit'], '25')

        # 3. Location, City, Jurisdiction
        self.assertIn('No. 25, Anna Nagar', entities['property_address'])
        self.assertEqual(entities['property_city'], 'Chennai')
        self.assertEqual(entities['jurisdiction'], 'Chennai')
        self.assertEqual(entities['execution_place'], 'Chennai')

        # 4. Durations & Dates
        self.assertEqual(entities['duration'], '11')
        self.assertEqual(entities['renewal_period'], '11')
        self.assertEqual(entities['notice_period'], "30 days'")
        self.assertEqual(entities['rent_due_date'], '5th')
        self.assertEqual(entities['start_date'], '1 December 2026')

        # 5. Generate and inspect agreement text
        doc_text = self.processor.generate_document('rental_agreement', entities, language='en')

        # Verify correct mappings in template
        self.assertIn('Mr. Rahul Sharma', doc_text)
        self.assertIn("called the 'Landlord'", doc_text)
        self.assertIn('Mr. Arjun Kumar', doc_text)
        self.assertIn('called the "Tenant"', doc_text)
        self.assertIn('Rs.15,000/- (Rupees Fifteen Thousand only)', doc_text)
        self.assertIn('Rs.50,000/- (Rupees Fifty Thousand only)', doc_text)
        self.assertIn('No. 25, Anna Nagar', doc_text)
        self.assertIn('Chennai', doc_text)
        self.assertIn('1 December 2026', doc_text)
        self.assertIn('5th of every month', doc_text)

        # Verify NO duplicate words
        self.assertNotIn('11 months months', doc_text)
        self.assertNotIn('months months', doc_text)
        self.assertNotIn('30 days months', doc_text)
        self.assertIn("30 days' written notice", doc_text)

    def test_role_reversal_sentence_structures(self):
        """Test that Landlord vs Tenant is correctly determined regardless of sentence order."""
        # Prompt A: Tenant comes first in the sentence
        prompt_a = (
            "Draft rental agreement for tenant Arjun Kumar and landlord Rahul Sharma "
            "for flat at No. 25, Anna Nagar, Chennai. Monthly rent: Rs. 15,000, deposit: Rs. 50,000 for 11 months."
        )
        ent_a = self.processor.extract_entities(prompt_a)
        self.assertEqual(ent_a['landlord'], 'Rahul Sharma')
        self.assertEqual(ent_a['tenant'], 'Arjun Kumar')

        # Prompt B: Explicit parenthetical roles: between A (Landlord) and B (Tenant)
        prompt_b = (
            "Agreement between Rahul Sharma (Landlord) and Arjun Kumar (Tenant) "
            "for premises in Chennai. Rent ₹15,000/month, deposit ₹50,000."
        )
        ent_b = self.processor.extract_entities(prompt_b)
        self.assertEqual(ent_b['landlord'], 'Rahul Sharma')
        self.assertEqual(ent_b['tenant'], 'Arjun Kumar')

        # Prompt C: "Mr. Rahul Sharma is the landlord, while Mr. Arjun Kumar is the tenant"
        prompt_c = (
            "Mr. Rahul Sharma is the landlord, while Mr. Arjun Kumar is the tenant. "
            "Property at No. 25, Anna Nagar, Chennai. Rent 15,000 rupees and deposit 50,000 rupees."
        )
        ent_c = self.processor.extract_entities(prompt_c)
        self.assertEqual(ent_c['landlord'], 'Rahul Sharma')
        self.assertEqual(ent_c['tenant'], 'Arjun Kumar')

    def test_currency_and_lakh_variations(self):
        """Test various currency symbols, word endings, and lakh formats."""
        # INR notation
        prompt_inr = "Rental agreement between landlord Rahul Sharma and tenant Arjun Kumar. Rent INR 15,000 pm, deposit INR 50,000 at Chennai."
        ent_inr = self.processor.extract_entities(prompt_inr)
        self.assertEqual(ent_inr['rent_amount'], '15,000')
        self.assertEqual(ent_inr['security_deposit'], '50,000')

        # Lakh notation
        prompt_lakh = "Agreement between landlord Rahul Sharma and tenant Arjun Kumar. Rent 15000 rupees per month, advance 0.5 lakh rupees in Bangalore."
        ent_lakh = self.processor.extract_entities(prompt_lakh)
        self.assertEqual(ent_lakh['rent_amount'], '15,000')
        self.assertEqual(ent_lakh['security_deposit'], '50,000')
        self.assertEqual(ent_lakh['security_deposit_words'], 'Fifty Thousand')

    def test_validation_guards(self):
        """Test validation rules when data is invalid or missing."""
        # Error: Landlord == Tenant
        same_parties = {
            'landlord': 'Rahul Sharma',
            'tenant': 'Rahul Sharma',
            'rent_amount': '15,000',
            'security_deposit': '50,000'
        }
        is_valid, errors, _ = self.processor.validate_entities('rental_agreement', same_parties)
        self.assertFalse(is_valid)
        self.assertIn("Landlord and Tenant cannot be the same person.", errors)

        # Warning: Missing fields use clean legal placeholders
        empty_prompt = "Create a rental agreement."
        ent_empty = self.processor.extract_entities(empty_prompt)
        self.assertEqual(ent_empty['landlord'], '[Landlord Name]')
        self.assertEqual(ent_empty['tenant'], '[Tenant Name]')
        self.assertEqual(ent_empty['rent_amount'], '[Rent Amount]')
        self.assertEqual(ent_empty['property_address'], '[Property Address]')

        doc = self.processor.generate_document('rental_agreement', ent_empty)
        self.assertIn('[Landlord Name]', doc)
        self.assertIn('[Tenant Name]', doc)


class TestFlaskIntegration(unittest.TestCase):
    def setUp(self):
        import importlib.util
        app_py_path = os.path.join(workspace_root, "app.py")
        spec = importlib.util.spec_from_file_location("main_app", app_py_path)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules["main_app"] = app_module
        spec.loader.exec_module(app_module)
        self.app = app_module.app
        self.client = self.app.test_client()

    def test_generate_from_prompt_route(self):
        """End-to-end test of the /generate_from_prompt route with the user sample."""
        prompt = (
            "Create a rental agreement where Landlord is Rahul Sharma and Tenant is Arjun Kumar. "
            "The property is at No. 25, Anna Nagar, Chennai, Tamil Nadu. "
            "Monthly rent is ₹15,000 and security deposit is ₹50,000. "
            "Agreement duration is 11 months starting from 1 December 2026. "
            "Rent due date is 5th of every month and notice period is 30 days."
        )
        response = self.client.post('/generate_from_prompt', data={'prompt': prompt}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Check that the preview workspace renders with the extracted values
        self.assertIn('Rahul Sharma', html)
        self.assertIn('Arjun Kumar', html)
        self.assertIn('15,000', html)
        self.assertIn('50,000', html)
        self.assertIn('No. 25, Anna Nagar', html)
        self.assertIn('Chennai', html)
        self.assertIn('1 December 2026', html)
        self.assertIn('doc-paper-wrapper', html)


if __name__ == '__main__':
    unittest.main()

