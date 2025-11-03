from datetime import datetime
import os
from typing import Dict, List, Optional
from jinja2 import Template, Environment
from jinja2.loaders import FileSystemLoader
from app.utils.template_validator import validate_template_data, fill_missing_variables

class DocumentGenerator:
    def __init__(self):
        self.base_template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        self.custom_template_dir = os.path.join(self.base_template_dir, 'custom')
        self.ta_template_dir = os.path.join(self.base_template_dir, 'ta')
        
        # Create custom templates directory if it doesn't exist
        os.makedirs(self.custom_template_dir, exist_ok=True)
        os.makedirs(os.path.join(self.custom_template_dir, 'versions'), exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(self.base_template_dir),
            trim_blocks=False,
            lstrip_blocks=False
        )

    def get_required_fields(self, doc_type: str) -> Dict[str, str]:
        """Get the required fields for a document type."""
        fields = {
            'house_lease': {
                'lessor': 'Lessor\'s Name',
                'lessor_age': 'Lessor\'s Age',
                'lessor_father': 'Lessor\'s Father Name',
                'lessor_address': 'Lessor\'s Address',
                'lessor_city': 'Lessor\'s City',
                'lessor_pincode': 'Lessor\'s Pincode',
                'lessee': 'Lessee\'s Name',
                'lessee_age': 'Lessee\'s Age',
                'lessee_father': 'Lessee\'s Father Name',
                'lessee_address': 'Lessee\'s Address',
                'lessee_city': 'Lessee\'s City',
                'lessee_pincode': 'Lessee\'s Pincode',
                'property_address': 'Property Address',
                'property_city': 'Property City',
                'property_pincode': 'Property Pincode',
                'lease_period': 'Lease Period (years)',
                'start_date': 'Start Date',
                'end_date': 'End Date',
                'lease_amount': 'Monthly Lease Amount',
                'lease_amount_words': 'Lease Amount in Words',
                'rent_due_date': 'Rent Due Date',
                'security_deposit': 'Security Deposit',
                'security_deposit_words': 'Security Deposit in Words',
                'notice_period': 'Notice Period (months)',
                'number_of_rooms': 'Number of Rooms'
            },
            'power_of_attorney': {
                'grantor_name': 'Grantor\'s Name',
                'attorney_name': 'Attorney\'s Name',
                'powers': 'Powers Granted'
            },
            'land_sale_deed': {
                'seller_name': 'Seller\'s Name',
                'buyer_name': 'Buyer\'s Name',
                'property_description': 'Property Description',
                'sale_amount': 'Sale Amount'
            },
            'rental_agreement': {
                'owner_name': 'Owner\'s Name',
                'renter_name': 'Renter\'s Name',
                'property_details': 'Property Details',
                'rental_amount': 'Monthly Rental Amount',
                'agreement_duration': 'Agreement Duration (months)'
            }
        }
        return fields.get(doc_type, {})

    def validate_fields(self, doc_type: str, data: Dict) -> List[str]:
        """Validate the provided fields and return a list of missing fields."""
        required_fields = self.get_required_fields(doc_type)
        missing_fields = []
        
        for field, display_name in required_fields.items():
            if field not in data or not data[field]:
                missing_fields.append(display_name)
                
        return missing_fields

    def _load_template(self, doc_type: str, language: str = 'en', custom_template: Optional[str] = None) -> Template:
        """Load the template file for the given document type and language."""
        if custom_template:
            template_path = os.path.join(self.custom_template_dir, custom_template)
            if not os.path.exists(template_path):
                raise ValueError(f"Custom template not found: {custom_template}")
            with open(template_path, 'r', encoding='utf-8') as f:
                return self.env.from_string(f.read())

        template_map = {
            'house_lease': 'house_lease_template.txt',
            'power_of_attorney': 'power_of_attorney_template.txt',
            'land_sale_deed': 'land_sale_deed_template.txt',
            'rental_agreement': 'rental_agreement_template.txt'
        }

        if doc_type not in template_map:
            raise ValueError(f"Invalid document type: {doc_type}")

        template_file_name = template_map[doc_type]
        
        # Use language subdirectory if exists, else fallback to base_template_dir
        template_dir = os.path.join(self.base_template_dir, language)
        template_full_path_lang = os.path.join(template_dir, template_file_name)
        template_relative_path_lang = os.path.join(language, template_file_name).replace(os.sep, '/')
        template_relative_path_base = template_file_name

        # Try loading language-specific template first
        if os.path.exists(template_full_path_lang): # Check if the language-specific file exists
            try:
                print(f"Attempting to load language-specific template: {template_relative_path_lang}")
                return self.env.get_template(template_relative_path_lang)
            except Exception as e:
                print(f"Error loading language-specific template '{template_relative_path_lang}': {e}. Falling back to base template.")
                return self.env.get_template(template_relative_path_base)
        else:
            print(f"Language-specific template file not found at '{template_full_path_lang}'. Falling back to base template.")
            return self.env.get_template(template_relative_path_base)

    def save_custom_template(self, filename: str, content: str) -> str:
        """Save a custom template and return its filename."""
        # Create a versioned filename to prevent overwrites
        base_name, ext = os.path.splitext(filename)
        version = 1
        while os.path.exists(os.path.join(self.custom_template_dir, f"{base_name}_v{version}{ext}")):
            version += 1
            
        new_filename = f"{base_name}_v{version}{ext}"
        file_path = os.path.join(self.custom_template_dir, new_filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return new_filename

    def generate_house_lease(self, data, language='en'):
        """Generate a house lease agreement."""
        template = self._load_template('house_lease', language)
        current_date = datetime.now().strftime("%B %d, %Y")
        data_with_date = data.copy()
        data_with_date['date'] = current_date
        
        # Validate template and fill missing variables
        try:
            # Read template content for validation
            template_file_name = 'house_lease_template.txt'
            if language != 'en':
                template_path = os.path.join(self.base_template_dir, language, template_file_name)
            else:
                template_path = os.path.join(self.base_template_dir, template_file_name)
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                validation_result = validate_template_data(template_content, data_with_date)
                
                if not validation_result['is_valid']:
                    print(f"Missing template variables: {validation_result['missing_variables']}")
                    data_with_date = fill_missing_variables(data_with_date, validation_result['missing_variables'], 'house_lease')
        except Exception as e:
            print(f"Template validation error: {e}")
            # Continue with original data if validation fails
        
        document = template.render(**data_with_date)
        
        return document

    def generate_power_of_attorney(self, data, language='en'):
        """Generate a power of attorney document."""
        template = self._load_template('power_of_attorney', language)
        current_date = datetime.now().strftime("%B %d, %Y")
        data_with_date = data.copy()
        data_with_date['date'] = current_date
        
        document = template.render(**data_with_date)
        
        return document

    def generate_land_sale_deed(self, data, language='en'):
        """Generate a land sale deed document."""
        template = self._load_template('land_sale_deed', language)
        current_date = datetime.now().strftime("%B %d, %Y")
        data_with_date = data.copy()
        data_with_date['date'] = current_date
        
        document = template.render(**data_with_date)
        
        return document

    def generate_rental_agreement(self, data, language='en'):
        """Generate a rental agreement document."""
        template = self._load_template('rental_agreement', language)
        current_date = datetime.now().strftime("%B %d, %Y")
        data_with_date = data.copy()
        data_with_date['date'] = current_date
        
        document = template.render(**data_with_date)
        
        return document

    def generate_document(self, doc_type, data, language='en'):
        """Generate a document based on the type and data provided."""
        generators = {
            'house_lease': self.generate_house_lease,
            'power_of_attorney': self.generate_power_of_attorney,
            'land_sale_deed': self.generate_land_sale_deed,
            'rental_agreement': self.generate_rental_agreement
        }
        
        if doc_type not in generators:
            raise ValueError(f"Invalid document type: {doc_type}")
            
        return generators[doc_type](data, language=language)
