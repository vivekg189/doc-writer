"""Template validation utilities for legal documents."""

import re
from typing import Dict, List, Set

def extract_template_variables(template_content: str) -> Set[str]:
    """Extract all Jinja2 template variables from template content."""
    # Pattern to match {{ variable_name }}
    pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
    variables = set(re.findall(pattern, template_content))
    return variables

def validate_template_data(template_content: str, data: Dict) -> Dict:
    """
    Validate that all template variables have corresponding data.
    Returns a dict with validation results.
    """
    template_vars = extract_template_variables(template_content)
    provided_vars = set(data.keys())
    
    missing_vars = template_vars - provided_vars
    extra_vars = provided_vars - template_vars
    
    return {
        'is_valid': len(missing_vars) == 0,
        'template_variables': template_vars,
        'provided_variables': provided_vars,
        'missing_variables': missing_vars,
        'extra_variables': extra_vars
    }

def fill_missing_variables(data: Dict, missing_vars: Set[str], doc_type: str = None) -> Dict:
    """Fill missing variables with appropriate legal placeholders."""
    filled_data = data.copy()
    from datetime import datetime
    now = datetime.now()
    
    # Default values for common variables
    defaults = {
        'date': str(now.day),
        'month': now.strftime("%B"), 
        'year': str(now.year),
        'execution_date': now.strftime("%d %B %Y"),
        'execution_place': '[Place]',
        'witness1_name': '[Witness 1 Name]',
        'witness1_address': '[Witness 1 Address]',
        'witness2_name': '[Witness 2 Name]',
        'witness2_address': '[Witness 2 Address]',
        'jurisdiction': '[Jurisdiction]'
    }
    
    # Document-specific defaults
    if doc_type == 'rental_agreement':
        defaults.update({
            'landlord': '[Landlord Name]',
            'landlord_age': '[Age]',
            'landlord_address': '[Landlord Address]',
            'landlord_city': '[City]',
            'landlord_pincode': '[Pincode]',
            'tenant': '[Tenant Name]',
            'tenant_father': '[Father\'s Name]',
            'tenant_age': '[Age]',
            'tenant_address': '[Tenant Address]',
            'tenant_city': '[City]',
            'tenant_pincode': '[Pincode]',
            'property_address': '[Property Address]',
            'property_city': '[City]',
            'property_pincode': '[Pincode]',
            'start_date': now.strftime("%d %B %Y"),
            'effective_date': now.strftime("%d %B %Y"),
            'duration': '11',
            'renewal_period': '11',
            'rent_amount': '[Rent Amount]',
            'rent_amount_words': '[Rent Amount in Words]',
            'rent_due_date': '5th',
            'rent_increase_percentage': '5',
            'security_deposit': '[Security Deposit]',
            'security_deposit_words': '[Security Deposit in Words]',
            'notice_period': '1 month\'s',
            'jurisdiction': '[Jurisdiction]',
            'witness1_name': '[Witness 1 Name]',
            'witness1_address': '[Witness 1 Address]',
            'witness2_name': '[Witness 2 Name]',
            'witness2_address': '[Witness 2 Address]',
            'execution_place': '[Place]'
        })
    elif doc_type == 'house_lease':
        defaults.update({
            'lessor': '[Lessor Name]',
            'lessor_age': '[Age]',
            'lessor_father': '[Father\'s Name]',
            'lessor_address': '[Address]',
            'lessor_city': '[City]',
            'lessor_pincode': '[Pincode]',
            'lessee': '[Lessee Name]',
            'lessee_age': '[Age]',
            'lessee_father': '[Father\'s Name]',
            'lessee_address': '[Address]',
            'lessee_city': '[City]',
            'lessee_pincode': '[Pincode]',
            'property_address': '[Property Address]',
            'property_city': '[City]',
            'property_pincode': '[Pincode]',
            'lease_period': '11 months',
            'start_date': now.strftime("%d %B %Y"),
            'end_date': '[End Date]',
            'lease_amount': '[Amount]',
            'lease_amount_words': '[Amount in Words]',
            'rent_due_date': '5th',
            'security_deposit': '[Security Deposit]',
            'security_deposit_words': '[Security Deposit in Words]',
            'notice_period': '1 month',
            'number_of_rooms': '[Number of Rooms]'
        })
    
    # Fill missing variables
    for var in missing_vars:
        if var in defaults:
            filled_data[var] = defaults[var]
        else:
            filled_data[var] = f'[{var.replace("_", " ").title()}]'
    
    return filled_data