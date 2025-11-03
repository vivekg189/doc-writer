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
    """Fill missing variables with appropriate default values."""
    filled_data = data.copy()
    
    # Default values for common variables
    defaults = {
        'date': 'Date not specified',
        'month': 'Month not specified', 
        'year': 'Year not specified',
        'execution_date': 'Date not specified',
        'execution_place': 'Place not specified',
        'witness1_name': 'Witness 1 name not specified',
        'witness1_address': 'Witness 1 address not specified',
        'witness2_name': 'Witness 2 name not specified',
        'witness2_address': 'Witness 2 address not specified',
        'jurisdiction': 'Jurisdiction not specified'
    }
    
    # Document-specific defaults
    if doc_type == 'house_lease':
        defaults.update({
            'lessor': 'Lessor name not specified',
            'lessor_age': 'Age not specified',
            'lessor_father': 'Father name not specified',
            'lessor_address': 'Address not specified',
            'lessor_city': 'City not specified',
            'lessor_pincode': 'Pincode not specified',
            'lessee': 'Lessee name not specified',
            'lessee_age': 'Age not specified',
            'lessee_father': 'Father name not specified',
            'lessee_address': 'Address not specified',
            'lessee_city': 'City not specified',
            'lessee_pincode': 'Pincode not specified',
            'property_address': 'Property address not specified',
            'property_city': 'Property city not specified',
            'property_pincode': 'Property pincode not specified',
            'lease_period': 'Lease period not specified',
            'start_date': 'Start date not specified',
            'end_date': 'End date not specified',
            'lease_amount': 'Amount not specified',
            'lease_amount_words': 'Amount in words not specified',
            'rent_due_date': 'Due date not specified',
            'security_deposit': 'Security deposit not specified',
            'security_deposit_words': 'Security deposit in words not specified',
            'notice_period': 'Notice period not specified',
            'number_of_rooms': 'Number of rooms not specified'
        })
    
    # Fill missing variables
    for var in missing_vars:
        if var in defaults:
            filled_data[var] = defaults[var]
        else:
            filled_data[var] = f'[{var} not specified]'
    
    return filled_data