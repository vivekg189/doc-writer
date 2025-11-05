-- Sample data for Legal Document Writer
-- Run this AFTER running supabase_schema.sql

-- Insert sample document templates (public templates)
INSERT INTO public.document_templates (id, user_id, name, document_type, language, template_content, is_public) VALUES
(
    uuid_generate_v4(),
    (SELECT id FROM auth.users LIMIT 1), -- Use first user or create a system user
    'Basic Rental Agreement',
    'rental_agreement',
    'en',
    'RENTAL AGREEMENT

This agreement is made on {{ date }} between:

Landlord: {{ landlord }} (Age: {{ landlord_age }}), Father: {{ landlord_father }}
Address: {{ landlord_address }}, {{ landlord_city }} - {{ landlord_pincode }}

Tenant: {{ tenant }} (Age: {{ tenant_age }}), Father: {{ tenant_father }}
Address: {{ tenant_address }}, {{ tenant_city }} - {{ tenant_pincode }}

Property: {{ property_address }}, {{ property_city }} - {{ property_pincode }}

Terms:
1) Rental Period: {{ duration }} months (Starting from {{ start_date }})
2) Monthly Rent: ₹ {{ rent_amount }} (In words: {{ rent_amount_words }})
3) Security Deposit: ₹ {{ security_deposit }} (In words: {{ security_deposit_words }})
4) Notice Period: {{ notice_period }} months

Witnesses:
1. {{ witness1_name }}, {{ witness1_address }}
2. {{ witness2_name }}, {{ witness2_address }}

Executed at {{ execution_place }} on {{ execution_date }}.',
    true
),
(
    uuid_generate_v4(),
    (SELECT id FROM auth.users LIMIT 1),
    'Basic Land Sale Deed',
    'land_sale_deed',
    'en',
    'SALE DEED

This deed is executed on {{ date }} between:

Seller: {{ seller }} (Age: {{ seller_age }}), Father: {{ seller_father }}
Address: {{ seller_address }}, {{ seller_city }} - {{ seller_pincode }}

Buyer: {{ buyer }} (Age: {{ buyer_age }}), Father: {{ buyer_father }}
Address: {{ buyer_address }}, {{ buyer_city }} - {{ buyer_pincode }}

Property Details:
Address: {{ property_address }}, {{ property_city }} - {{ property_pincode }}
Survey Number: {{ survey_number }}
Area: {{ area }} sq ft
Boundaries: North - {{ north_boundary }}, South - {{ south_boundary }}, East - {{ east_boundary }}, West - {{ west_boundary }}

Sale Amount: ₹ {{ sale_amount }} (In words: {{ sale_amount_words }})

Witnesses:
1. {{ witness1_name }}, {{ witness1_address }}
2. {{ witness2_name }}, {{ witness2_address }}

Executed at {{ execution_place }} on {{ execution_date }}.',
    true
);

-- Note: Sample user history will be created automatically when users perform actions