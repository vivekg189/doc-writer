import os
import re
from datetime import datetime
from jinja2 import Template
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

# Load spaCy model for NLP processing
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except (OSError, ImportError):
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    import spacy
    nlp = spacy.load("en_core_web_sm")

from app.services.document_generator import DocumentGenerator

MAJOR_INDIAN_CITIES = [
    'Bangalore', 'Bengaluru', 'Chennai', 'Madras', 'Mumbai', 'Bombay', 'Delhi', 'New Delhi',
    'Hyderabad', 'Kolkata', 'Calcutta', 'Pune', 'Ahmedabad', 'Jaipur', 'Surat', 'Lucknow',
    'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara',
    'Ghaziabad', 'Ludhiana', 'Coimbatore', 'Agra', 'Madurai', 'Nashik', 'Vijayawada',
    'Faridabad', 'Meerut', 'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad',
    'Amritsar', 'Navi Mumbai', 'Allahabad', 'Prayagraj', 'Ranchi', 'Howrah', 'Jabalpur',
    'Gwalior', 'Mysore', 'Mysuru', 'Kochi', 'Cochin', 'Chandigarh', 'Noida', 'Gurgaon', 'Gurugram'
]

INDIAN_STATES = [
    'Tamil Nadu', 'Karnataka', 'Maharashtra', 'Telangana', 'Andhra Pradesh',
    'Kerala', 'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'Madhya Pradesh',
    'West Bengal', 'Bihar', 'Punjab', 'Haryana', 'Delhi', 'Odisha', 'Assam', 'Goa'
]

SUPPORTED_LANGUAGES = {
    'english': 'en', 'en': 'en',
    'hindi': 'hi', 'hi': 'hi',
    'tamil': 'ta', 'ta': 'ta',
    'telugu': 'te', 'te': 'te',
    'kannada': 'kn', 'kn': 'kn',
    'marathi': 'mr', 'mr': 'mr',
    'bengali': 'bn', 'bn': 'bn', 'bangla': 'bn',
    'gujarati': 'gu', 'gu': 'gu',
    'odia': 'or', 'or': 'or', 'oriya': 'or',
    'urdu': 'ur', 'ur': 'ur'
}


def number_to_words_indian(num_val):
    """Convert an integer amount into Indian numbering system words representation."""
    try:
        if isinstance(num_val, str):
            clean_str = num_val.replace(',', '').strip()
            num = int(round(float(clean_str)))
        else:
            num = int(round(float(num_val)))
    except (ValueError, TypeError):
        return str(num_val)

    if num == 0:
        return "Zero"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _two_digits(n):
        if n < 20:
            return units[n]
        return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")

    def _three_digits(n):
        if n < 100:
            return _two_digits(n)
        return units[n // 100] + " Hundred" + (" and " + _two_digits(n % 100) if n % 100 != 0 else "")

    parts = []
    # Crores (1,00,00,000)
    crores = num // 10000000
    if crores > 0:
        parts.append(_three_digits(crores) + " Crore")
        num %= 10000000

    # Lakhs (1,00,000)
    lakhs = num // 100000
    if lakhs > 0:
        parts.append(_two_digits(lakhs) + " Lakh")
        num %= 100000

    # Thousands (1,000)
    thousands = num // 1000
    if thousands > 0:
        parts.append(_two_digits(thousands) + " Thousand")
        num %= 1000

    # Remainder (Hundreds and tens)
    if num > 0:
        parts.append(_three_digits(num))

    return " ".join(parts).strip()


def parse_indian_amount(raw_str):
    """Parse Indian currency amount string (₹15,000, 1.5 lakh, Rs 15000) into (clean_int_str, words)."""
    if not raw_str:
        return None, None
    raw_str = str(raw_str).strip()

    # Check for lakh representation: e.g. "1.5 lakh", "0.5 lakh", "1.5 lakhs"
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lakhs)', raw_str, re.IGNORECASE)
    if lakh_match:
        try:
            val = int(round(float(lakh_match.group(1)) * 100000))
            return f"{val:,}", number_to_words_indian(val)
        except ValueError:
            pass

    # Extract digits with optional commas and decimals (e.g. from "Rs. 50,000", "₹15,000", "INR 15000")
    num_match = re.search(r'(\d{1,3}(?:,\d{2,3})+|\d+)(?:\.(\d+))?', raw_str)
    if num_match:
        integer_part = num_match.group(1).replace(',', '')
        try:
            val = int(integer_part)
            return f"{val:,}", number_to_words_indian(val)
        except ValueError:
            pass

    return raw_str, None


class LegalDocumentProcessor:
    def __init__(self):
        self.document_types = {
            'rental_agreement': {
                'keywords': ['rental', 'rent', 'lease', 'tenant', 'landlord', 'monthly'],
                'required_fields': ['landlord', 'tenant', 'property_address', 'rent_amount', 'duration'],
                'template': 'rental_agreement_template.txt'
            },
            'land_sale_deed': {
                'keywords': ['sale', 'deed', 'property', 'buyer', 'seller', 'purchase'],
                'required_fields': ['seller', 'buyer', 'property_address', 'sale_amount'],
                'template': 'land_sale_deed_template.txt'
            },
            'power_of_attorney': {
                'keywords': ['power', 'attorney', 'delegate', 'authority', 'behalf'],
                'required_fields': ['principal', 'attorney', 'matter_description', 'effective_date'],
                'template': 'power_of_attorney_template.txt'
            },
            'house_lease': {
                'keywords': ['house', 'lease', 'lessor', 'lessee', 'property'],
                'required_fields': ['lessor', 'lessee', 'property_address', 'lease_amount', 'lease_period'],
                'template': 'house_lease_template.txt'
            }
        }
        self.document_generator = DocumentGenerator()

    def classify_document_type(self, prompt):
        """Classify the document type based on user's prompt."""
        prompt_lower = prompt.lower()
        scores = {}
        for doc_type, info in self.document_types.items():
            score = sum(1 for keyword in info['keywords'] if keyword in prompt_lower)
            scores[doc_type] = score

        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'rental_agreement'

    def extract_language(self, prompt):
        """Extract requested document language without confusing cities or other keywords."""
        match = re.search(r'\b(?:in\s+language|language\s*[:=-]|in)\s+([a-zA-Z]+)\b', prompt, re.IGNORECASE)
        if match:
            candidate = match.group(1).lower()
            if candidate in SUPPORTED_LANGUAGES:
                return SUPPORTED_LANGUAGES[candidate]
        return 'en'

    def _clean_person_name(self, name):
        """Clean titles, prefixes, and residual role labels from person names."""
        if not name:
            return ""
        name = re.sub(r'^(?:(?:draft\s+)?(?:rental\s+)?agreement\s+(?:between|for)|between|for|with|and)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'^(?:Mr\.?|Mrs\.?|Ms\.?|Shri|Dr\.?)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[\(\[\{]?(?:the\s+)?(?:landlord|tenant|owner|renter|lessor|lessee|buyer|seller|principal|attorney)[\)\]\}]?', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+as\s+(?:the\s+)?(?:landlord|tenant|owner|renter|lessor|lessee|buyer|seller|principal|attorney)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[,:\-]', '', name)
        return name.strip()

    def _is_valid_person_name(self, name):
        """Ensure candidate name is a plausible person name and not a location or role keyword."""
        if not name:
            return False
        clean = name.strip()
        words = clean.lower().split()
        if not words or len(words) < 1:
            return False
        invalid_words = {
            'landlord', 'tenant', 'owner', 'renter', 'lessor', 'lessee',
            'property', 'address', 'agreement', 'rental', 'lease',
            'nagar', 'road', 'street', 'colony', 'enclave', 'layout', 'sector',
            'phase', 'floor', 'block', 'apartments', 'apartment', 'chennai',
            'bangalore', 'bengaluru', 'mumbai', 'delhi', 'hyderabad', 'nadu',
            'tamil', 'karnataka', 'maharashtra'
        }
        if any(w in invalid_words for w in words):
            return False
        return True

    def extract_parties(self, prompt):
        """Extract landlord and tenant based on contextual roles, patterns, and keywords."""
        landlord = None
        tenant = None

        # Pattern 1: Parenthetical roles: "Person (Landlord)", "Person (Tenant)"
        p_landlord = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[\(\[\{]\s*(?i:(?:the\s+)?(?:landlord|owner|lessor))\s*[\)\]\}]', prompt)
        if p_landlord:
            cand = self._clean_person_name(p_landlord.group(1))
            if self._is_valid_person_name(cand):
                landlord = cand

        p_tenant = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[\(\[\{]\s*(?i:(?:the\s+)?(?:tenant|renter|lessee))\s*[\)\]\}]', prompt)
        if p_tenant:
            cand = self._clean_person_name(p_tenant.group(1))
            if self._is_valid_person_name(cand):
                tenant = cand

        # Pattern 2: Keyword prefix: "Landlord: Rahul Sharma", "Landlord is Rahul Sharma", "landlord Rahul Sharma"
        if not landlord:
            m = re.search(r'(?i:\b(?:landlord|owner|lessor)(?:\s+name)?\s*[:\-]?\s*(?:is\s+)?(?:Mr\.?|Mrs\.?|Ms\.?|Shri)?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', prompt)
            if m:
                cand = self._clean_person_name(m.group(1))
                if self._is_valid_person_name(cand):
                    landlord = cand

        # Pattern 3: Keyword prefix: "Tenant: Arjun Kumar", "Tenant is Arjun Kumar", "tenant Arjun Kumar"
        if not tenant:
            m = re.search(r'(?i:\b(?:tenant|renter|lessee)(?:\s+name)?\s*[:\-]?\s*(?:is\s+)?(?:Mr\.?|Mrs\.?|Ms\.?|Shri)?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', prompt)
            if m:
                cand = self._clean_person_name(m.group(1))
                if self._is_valid_person_name(cand):
                    tenant = cand

        # Pattern 4: Suffix: "Rahul Sharma is the landlord, while Arjun Kumar is the tenant"
        if not landlord:
            m = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?i:is\s+(?:the\s+)?(?:landlord|owner|lessor))', prompt)
            if m:
                cand = self._clean_person_name(m.group(1))
                if self._is_valid_person_name(cand):
                    landlord = cand

        if not tenant:
            m = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?i:is\s+(?:the\s+)?(?:tenant|renter|lessee))', prompt)
            if m:
                cand = self._clean_person_name(m.group(1))
                if self._is_valid_person_name(cand):
                    tenant = cand

        # Pattern 5: "between Person A and Person B"
        if not landlord or not tenant:
            m = re.search(r'(?i:\bbetween\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?i:and\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', prompt)
            if m:
                c1 = self._clean_person_name(m.group(1))
                c2 = self._clean_person_name(m.group(2))
                if self._is_valid_person_name(c1) and self._is_valid_person_name(c2):
                    if not landlord and not tenant:
                        landlord, tenant = c1, c2
                    elif not landlord and c2 == tenant:
                        landlord = c1
                    elif not tenant and c1 == landlord:
                        tenant = c2

        # Fallback using spaCy PERSON entities if not yet detected
        if not landlord or not tenant:
            doc = nlp(prompt)
            persons = []
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    clean_p = self._clean_person_name(ent.text)
                    if self._is_valid_person_name(clean_p) and clean_p.lower() not in ['landlord', 'tenant', 'owner', 'renter']:
                        if clean_p not in persons:
                            persons.append(clean_p)

            if len(persons) >= 2:
                if not landlord:
                    landlord = persons[0]
                if not tenant and persons[1] != landlord:
                    tenant = persons[1]
            elif len(persons) == 1:
                if not landlord:
                    landlord = persons[0]
                elif not tenant and persons[0] != landlord:
                    tenant = persons[0]

        return landlord, tenant

    def extract_financials(self, prompt):
        """Extract monthly rent and security deposit amounts accurately."""
        rent_amount = None
        security_deposit = None

        # 1. Security Deposit / Advance Extraction (check lakh first)
        deposit_patterns = [
            r'(?:security\s+deposit|deposit|advance|premium\s+advance)(?:\s+amount|\s+is|\s+of|\s*[:=-])?\s*(?:Rs\.?|INR|\u20b9)?\s*(\d+(?:\.\d+)?\s*lakhs?|\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupees)?',
            r'(?:Rs\.?|INR|\u20b9)?\s*(\d+(?:\.\d+)?\s*lakhs?|\d+(?:,\d+)*(?:\.\d+)?)\s*(?:/-)?\s*(?:as\s+(?:security\s+)?deposit|as\s+advance|deposit)'
        ]
        for pat in deposit_patterns:
            m = re.search(pat, prompt, re.IGNORECASE)
            if m:
                raw_dep = m.group(1)
                security_deposit, _ = parse_indian_amount(raw_dep)
                break

        # 2. Monthly Rent Extraction (check lakh first)
        rent_patterns = [
            r'(?:monthly\s+)?rent(?:\s+amount|\s+is|\s+of|\s*[:=-])?\s*(?:Rs\.?|INR|\u20b9)?\s*(\d+(?:\.\d+)?\s*lakhs?|\d+(?:,\d+)*(?:\.\d+)?)\s*(?:per\s+month|/month|pm|rupees)?',
            r'(?:Rs\.?|INR|\u20b9)\s*(\d+(?:\.\d+)?\s*lakhs?|\d+(?:,\d+)*(?:\.\d+)?)\s*(?:/-)?\s*(?:per\s+month|monthly|/month|pm)',
            r'(\d+(?:\.\d+)?\s*lakhs?|\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupees|Rs\.?|INR|\u20b9)?\s*(?:per\s+month|monthly|/month|pm)'
        ]
        for pat in rent_patterns:
            m = re.search(pat, prompt, re.IGNORECASE)
            if m:
                raw_rent = m.group(1)
                rent_amount, _ = parse_indian_amount(raw_rent)
                break

        # General Currency Fallback if either is missing
        if not rent_amount or not security_deposit:
            all_currencies = re.findall(r'(?:Rs\.?|INR|\u20b9)\s*(\d+(?:\.\d+)?\s*lakhs?|\d+(?:,\d+)*(?:\.\d+)?)', prompt, re.IGNORECASE)
            for c_match in all_currencies:
                clean_c, _ = parse_indian_amount(c_match)
                if not rent_amount:
                    rent_amount = clean_c
                elif not security_deposit and clean_c != rent_amount:
                    try:
                        c_val = int(clean_c.replace(',', ''))
                        r_val = int(rent_amount.replace(',', ''))
                        if c_val > r_val:
                            security_deposit = clean_c
                    except ValueError:
                        pass

        rent_words = number_to_words_indian(rent_amount) if rent_amount else None
        deposit_words = number_to_words_indian(security_deposit) if security_deposit else None

        return rent_amount, rent_words, security_deposit, deposit_words

    def extract_durations_and_notice(self, prompt):
        """Extract agreement duration, renewal duration, and notice period without duplicates."""
        duration = None
        renewal_period = None
        notice_period = None

        # Agreement Duration: e.g. "11 months", "1 year"
        dur_match = re.search(r'\b(?:duration|period)(?:\s+of|\s+is|\s*[:=-])?\s*(\d+)\s*(?:months?|years?)', prompt, re.IGNORECASE)
        if not dur_match:
            dur_match = re.search(r'\bfor\s+(\d+)\s*months?\b', prompt, re.IGNORECASE)
        if not dur_match:
            dur_match = re.search(r'\b(\d+)\s*months?\s*(?:duration|period|agreement|lease)\b', prompt, re.IGNORECASE)
        if not dur_match:
            dur_match = re.search(r'\b(\d+)\s*months?\b', prompt, re.IGNORECASE)

        if dur_match:
            duration = dur_match.group(1).strip()
        else:
            duration = "11"

        renewal_period = duration

        # Notice Period: e.g. "30 days", "1 month"
        notice_match = re.search(r'(?:notice\s+period|notice)(?:\s+(?:is|of))?\s*[:=-]?\s*(\d+\s*(?:days?|months?))', prompt, re.IGNORECASE)
        if not notice_match:
            notice_match = re.search(r'\b(\d+\s*(?:days?|months?))\s+notice\b', prompt, re.IGNORECASE)

        if notice_match:
            raw_notice = notice_match.group(1).strip().lower()
            if 'day' in raw_notice:
                notice_period = f"{raw_notice}'"
            elif 'month' in raw_notice:
                notice_period = f"{raw_notice}'s"
            else:
                notice_period = f"{raw_notice} written notice"
        else:
            notice_period = "1 month's"

        return duration, renewal_period, notice_period

    def extract_location_and_property(self, prompt):
        """Extract property address, city, state, jurisdiction, and execution place."""
        property_address = None
        property_city = None
        property_state = None

        # Detect City from known list
        for city in MAJOR_INDIAN_CITIES:
            if re.search(r'\b' + re.escape(city) + r'\b', prompt, re.IGNORECASE):
                property_city = city
                break

        # Detect State from known list
        for state in INDIAN_STATES:
            if re.search(r'\b' + re.escape(state) + r'\b', prompt, re.IGNORECASE):
                property_state = state
                break

        # Extract detailed property address: e.g. "No. 25, Anna Nagar, Chennai, Tamil Nadu"
        prop_patterns = [
            r'(?:property|premises|flat|house|apartment)(?:\s+(?:is|located|address))?\s*(?:is|at|in|[:=-])\s*(No\.?\s*[^.\n]+|[A-Za-z0-9\s,\-#]+?(?:Nagar|Road|Street|Apartments|Layout|Colony|Enclave|Sector|Phase|Floor|Block)[^.\n]*)',
            r'\bat\s+(No\.?\s*[^.\n]+|[A-Za-z0-9\s,\-#]+?(?:Nagar|Road|Street|Apartments|Layout|Colony|Enclave|Sector|Phase|Floor|Block)[^.\n]*)',
            r'\bfor\s+(?:flat|house|apartment|premises)\s+(?:at|in)\s+([^.\n]+?)(?=\s*(?:\.|$|\brent\b|\bdeposit\b|\bfor\s+\d+))'
        ]

        for pat in prop_patterns:
            m = re.search(pat, prompt, re.IGNORECASE)
            if m:
                cand = m.group(1).strip(' ,.')
                cand = re.sub(r'\s*(?:Monthly\s+)?rent.*$', '', cand, flags=re.IGNORECASE).strip(' ,.')
                cand = re.sub(r'\s*(?:security\s+)?deposit.*$', '', cand, flags=re.IGNORECASE).strip(' ,.')
                cand = re.sub(r'\s*for\s+\d+.*$', '', cand, flags=re.IGNORECASE).strip(' ,.')
                if len(cand) > 3 and not cand.lower().startswith(('the', 'an', 'a')):
                    property_address = cand
                    break

        if not property_address:
            # Fallback to city/state combo
            if property_city and property_state:
                property_address = f"Premises in {property_city}, {property_state}"
            elif property_city:
                property_address = f"Premises in {property_city}"
            else:
                property_address = "[Property Address]"

        jurisdiction = property_city or "[Jurisdiction]"
        execution_place = property_city or "[Place]"

        return property_address, property_city or "[City]", property_state, jurisdiction, execution_place

    def extract_dates_and_payment(self, prompt):
        """Extract start date, execution date, and rent due payment date."""
        start_date = None
        date_day = None
        date_month = None
        date_year = None
        rent_due_date = "5th"

        # Start Date
        start_date_patterns = [
            r'(?:starting|commencing|effective|start\s+date)(?:\s+from|\s+on|\s*[:=-])?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})',
            r'(?:starting|commencing|effective|from)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        ]

        for pat in start_date_patterns:
            m = re.search(pat, prompt, re.IGNORECASE)
            if m:
                start_date = m.group(1).strip()
                break

        now = datetime.now()
        if start_date:
            # Parse day, month, year
            parts = re.split(r'[\s,]+', start_date)
            if len(parts) >= 3:
                date_day = parts[0]
                date_month = parts[1]
                date_year = parts[2]
        else:
            start_date = now.strftime("%d %B %Y")
            date_day = str(now.day)
            date_month = now.strftime("%B")
            date_year = str(now.year)

        # Rent Due Date: e.g. "5th of every month" or "5th"
        due_match = re.search(r'(?:rent\s+(?:payable|payment|due)?\s*(?:on|by|before)?|due\s+date\s*[:=-]?)\s*(\d{1,2}(?:st|nd|rd|th)?|\d{1,2})\b', prompt, re.IGNORECASE)
        if due_match:
            rent_due_date = due_match.group(1).strip()
            if not re.search(r'(?:st|nd|rd|th)$', rent_due_date, re.IGNORECASE):
                day_num = int(rent_due_date)
                if 11 <= day_num <= 13:
                    rent_due_date = f"{day_num}th"
                else:
                    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
                    rent_due_date = f"{day_num}{suffixes.get(day_num % 10, 'th')}"

        return start_date, date_day, date_month, date_year, rent_due_date

    def extract_entities(self, prompt):
        """Extract structured legal entities using contextual NLP rules and spaCy verification."""
        entities = {}
        prompt_clean = prompt.strip()

        # 1. Extract Parties (Landlord & Tenant)
        landlord, tenant = self.extract_parties(prompt_clean)
        entities['landlord'] = landlord or '[Landlord Name]'
        entities['tenant'] = tenant or '[Tenant Name]'

        # 2. Extract Financials (Rent & Deposit)
        rent, rent_words, deposit, deposit_words = self.extract_financials(prompt_clean)
        entities['rent_amount'] = rent or '[Rent Amount]'
        entities['rent_amount_words'] = rent_words or '[Rent Amount in Words]'
        entities['security_deposit'] = deposit or '[Security Deposit]'
        entities['security_deposit_words'] = deposit_words or '[Security Deposit in Words]'

        # 3. Extract Durations & Notice Period
        duration, renewal_period, notice_period = self.extract_durations_and_notice(prompt_clean)
        entities['duration'] = duration
        entities['renewal_period'] = renewal_period
        entities['notice_period'] = notice_period

        # 4. Extract Location, City, State & Jurisdiction
        prop_addr, city, state, jurisdiction, exec_place = self.extract_location_and_property(prompt_clean)
        entities['property_address'] = prop_addr
        entities['property_city'] = city
        entities['jurisdiction'] = jurisdiction
        entities['execution_place'] = exec_place
        entities['landlord_city'] = city
        entities['tenant_city'] = city

        # 5. Extract Dates
        start_date, d_day, d_month, d_year, due_date = self.extract_dates_and_payment(prompt_clean)
        entities['start_date'] = start_date
        entities['effective_date'] = start_date
        entities['execution_date'] = start_date
        entities['date'] = d_day
        entities['month'] = d_month
        entities['year'] = d_year
        entities['rent_due_date'] = due_date

        # 6. Standard Legal Clauses & Percentages
        entities['rent_increase_percentage'] = '5'
        entities['landlord_age'] = '[Age]'
        entities['landlord_address'] = '[Landlord Address]'
        entities['landlord_pincode'] = '[Pincode]'
        entities['tenant_father'] = '[Father\'s Name]'
        entities['tenant_age'] = '[Age]'
        entities['tenant_address'] = '[Tenant Address]'
        entities['tenant_pincode'] = '[Pincode]'
        entities['property_pincode'] = '[Pincode]'
        entities['witness1_name'] = '[Witness 1 Name]'
        entities['witness1_address'] = '[Witness 1 Address]'
        entities['witness2_name'] = '[Witness 2 Name]'
        entities['witness2_address'] = '[Witness 2 Address]'

        return entities

    def validate_entities(self, doc_type, entities):
        """Validate extracted legal data for correctness before generation."""
        errors = []
        warnings = []

        if doc_type == 'rental_agreement':
            landlord = str(entities.get('landlord', '')).strip().lower()
            tenant = str(entities.get('tenant', '')).strip().lower()

            if landlord and tenant and landlord != '[landlord name]' and tenant != '[tenant name]' and landlord == tenant:
                errors.append("Landlord and Tenant cannot be the same person.")

            rent = str(entities.get('rent_amount', '')).replace(',', '').strip()
            if rent and rent != '[rent amount]':
                try:
                    if float(rent) <= 0:
                        errors.append("Monthly rent must be greater than zero.")
                except ValueError:
                    pass

            deposit = str(entities.get('security_deposit', '')).replace(',', '').strip()
            if deposit and deposit != '[security deposit]':
                try:
                    if float(deposit) < 0:
                        errors.append("Security deposit cannot be negative.")
                except ValueError:
                    pass

            # Check mandatory presence
            if not entities.get('landlord') or entities['landlord'] == '[Landlord Name]':
                warnings.append("Landlord name was not found in prompt.")
            if not entities.get('tenant') or entities['tenant'] == '[Tenant Name]':
                warnings.append("Tenant name was not found in prompt.")
            if not entities.get('rent_amount') or entities['rent_amount'] == '[Rent Amount]':
                warnings.append("Rent amount was not found in prompt.")

        return len(errors) == 0, errors, warnings

    def identify_missing_fields(self, doc_type, entities):
        """Identify missing required fields for the document type."""
        required = self.document_types.get(doc_type, {}).get('required_fields', [])
        missing = []
        for f in required:
            val = entities.get(f)
            if not val or str(val).startswith('['):
                missing.append(f)
        return missing

    def generate_document(self, doc_type, entities, language='en'):
        """Generate document content using DocumentGenerator."""
        if doc_type not in self.document_types:
            raise ValueError(f"Unsupported document type: {doc_type}")
        return self.document_generator.generate_document(doc_type, entities, language)

    def generate_docx(self, content, filename):
        """Generate a .docx file from document content."""
        doc = Document()
        doc.add_heading('Legal Document', 0)
        for para in content.split('\n\n'):
            if para.strip():
                doc.add_paragraph(para.strip())
        doc.save(filename)

    def generate_pdf(self, content, filename):
        """Generate a .pdf file from document content."""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        for para in content.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
        doc.build(story)
