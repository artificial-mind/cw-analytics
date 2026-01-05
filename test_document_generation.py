"""
Test Document Generation
Test the document generator directly before integrating with API
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from documents.generator_reportlab import get_document_generator

def test_bill_of_lading():
    """Test Bill of Lading generation."""
    print("\n" + "="*60)
    print("Testing Bill of Lading Generation")
    print("="*60)
    
    generator = get_document_generator()
    
    data = {
        "shipment_id": "job-2025-001",
        "carrier_name": "MAERSK LINE",
        "carrier_address": "123 Shipping Lane, Copenhagen, Denmark",
        "vessel_name": "MSC GULSUN",
        "voyage_number": "123W",
        "port_of_loading": "Shanghai, China",
        "port_of_discharge": "Los Angeles, USA",
        "shipper_name": "ABC Electronics Corp",
        "shipper_address": "789 Factory Road",
        "shipper_city": "Shanghai",
        "shipper_country": "China",
        "consignee_name": "XYZ Import Inc",
        "consignee_address": "456 Import Avenue",
        "consignee_city": "Los Angeles, CA",
        "consignee_country": "USA",
        "containers": [
            {
                "number": "MSCU1234567",
                "seal_number": "SEAL001",
                "type": "40HC",
                "package_count": 500,
                "package_type": "CARTONS",
                "description": "Electronic Components - Laptops",
                "weight": 15000,
                "volume": 67.5
            },
            {
                "number": "MSCU7654321",
                "seal_number": "SEAL002",
                "type": "40HC",
                "package_count": 300,
                "package_type": "PALLETS",
                "description": "Computer Accessories",
                "weight": 12000,
                "volume": 65.0
            }
        ]
    }
    
    result = generator.generate_bill_of_lading(data)
    
    if result["success"]:
        print(f"✅ BOL Generated Successfully!")
        print(f"   Document Number: {result['document_number']}")
        print(f"   File Path: {result['file_path']}")
        print(f"   File Size: {result['file_size_kb']} KB")
        print(f"   Document URL: {result['document_url']}")
    else:
        print(f"❌ BOL Generation Failed: {result.get('error')}")
    
    return result


def test_commercial_invoice():
    """Test Commercial Invoice generation."""
    print("\n" + "="*60)
    print("Testing Commercial Invoice Generation")
    print("="*60)
    
    generator = get_document_generator()
    
    data = {
        "shipment_id": "job-2025-001",
        "invoice_number": "INV-2025-001",
        "po_number": "PO-12345",
        "exporter_name": "ABC Electronics Corp",
        "exporter_address": "789 Factory Road",
        "exporter_city": "Shanghai",
        "exporter_country": "China",
        "exporter_tax_id": "CHN-12345678",
        "exporter_phone": "+86-21-1234-5678",
        "importer_name": "XYZ Import Inc",
        "importer_address": "456 Import Avenue",
        "importer_city": "Los Angeles",
        "importer_state": "CA",
        "importer_postal_code": "90001",
        "importer_country": "USA",
        "importer_tax_id": "US-87654321",
        "importer_phone": "+1-310-555-1234",
        "currency": "USD",
        "incoterms": "FOB Shanghai",
        "payment_terms": "NET 30",
        "country_of_origin": "China",
        "line_items": [
            {
                "description": "Laptop Computer - Model X1",
                "part_number": "LAP-X1-001",
                "hs_code": "8471.30.0100",
                "quantity": 500,
                "unit": "PCS",
                "unit_price": 450.00,
                "country_of_origin": "China"
            },
            {
                "description": "Wireless Mouse",
                "part_number": "MOU-W1-002",
                "hs_code": "8471.60.7000",
                "quantity": 1000,
                "unit": "PCS",
                "unit_price": 15.00,
                "country_of_origin": "China"
            },
            {
                "description": "USB-C Cable",
                "part_number": "CAB-UC-003",
                "hs_code": "8544.42.2000",
                "quantity": 2000,
                "unit": "PCS",
                "unit_price": 5.00,
                "country_of_origin": "China"
            }
        ],
        "freight_charges": 3500.00,
        "insurance_charges": 500.00,
        "discount_percentage": 5,
        "vat_percentage": 0,  # No VAT for international
        "payment_instructions": True,
        "bank_name": "Bank of China",
        "account_name": "ABC Electronics Corp",
        "account_number": "1234567890",
        "swift_code": "BKCHCNBJ450",
        "bank_address": "Shanghai Branch, China",
        "notes": "Goods must be inspected within 5 days of delivery"
    }
    
    result = generator.generate_commercial_invoice(data)
    
    if result["success"]:
        print(f"✅ Invoice Generated Successfully!")
        print(f"   Invoice Number: {result['invoice_number']}")
        print(f"   File Path: {result['file_path']}")
        print(f"   File Size: {result['file_size_kb']} KB")
        print(f"   Total Amount: {result['currency']} {result['total_amount']:.2f}")
    else:
        print(f"❌ Invoice Generation Failed: {result.get('error')}")
    
    return result


def test_packing_list():
    """Test Packing List generation."""
    print("\n" + "="*60)
    print("Testing Packing List Generation")
    print("="*60)
    
    generator = get_document_generator()
    
    data = {
        "shipment_id": "job-2025-001",
        "packing_list_number": "PKG-2025-001",
        "invoice_number": "INV-2025-001",
        "bl_number": "BOL-job-2025-001",
        "container_number": "MSCU1234567",
        "shipper_name": "ABC Electronics Corp",
        "shipper_address": "789 Factory Road",
        "shipper_city": "Shanghai",
        "shipper_country": "China",
        "shipper_contact": "+86-21-1234-5678",
        "consignee_name": "XYZ Import Inc",
        "consignee_address": "456 Import Avenue",
        "consignee_city": "Los Angeles, CA",
        "consignee_country": "USA",
        "consignee_contact": "+1-310-555-1234",
        "port_of_loading": "Shanghai, China",
        "port_of_discharge": "Los Angeles, USA",
        "packages": [
            {
                "package_id": "PKG-001",
                "package_type": "CARTON",
                "marks": "ABC/XYZ-001",
                "length": 120,
                "width": 80,
                "height": 100,
                "volume": 0.96,
                "gross_weight": 250.5,
                "net_weight": 240.0,
                "items": [
                    {
                        "description": "Laptop Computer - Model X1",
                        "part_number": "LAP-X1-001",
                        "quantity": 100,
                        "unit_weight": 2.4,
                        "total_weight": 240.0
                    }
                ]
            },
            {
                "package_id": "PKG-002",
                "package_type": "CARTON",
                "marks": "ABC/XYZ-002",
                "length": 100,
                "width": 60,
                "height": 80,
                "volume": 0.48,
                "gross_weight": 150.8,
                "net_weight": 145.0,
                "items": [
                    {
                        "description": "Wireless Mouse",
                        "part_number": "MOU-W1-002",
                        "quantity": 500,
                        "unit_weight": 0.15,
                        "total_weight": 75.0
                    },
                    {
                        "description": "USB-C Cable",
                        "part_number": "CAB-UC-003",
                        "quantity": 1000,
                        "unit_weight": 0.07,
                        "total_weight": 70.0
                    }
                ]
            }
        ],
        "special_instructions": "Handle with care - Electronic equipment inside",
        "is_fragile": True,
        "marks_and_numbers": "ABC Electronics Corp\nShanghai, China\nPO: 12345\nDEST: Los Angeles, USA"
    }
    
    result = generator.generate_packing_list(data)
    
    if result["success"]:
        print(f"✅ Packing List Generated Successfully!")
        print(f"   Packing List Number: {result['packing_list_number']}")
        print(f"   File Path: {result['file_path']}")
        print(f"   File Size: {result['file_size_kb']} KB")
        print(f"   Total Packages: {result['total_packages']}")
        print(f"   Total Weight: {result['total_weight_kg']} KG")
    else:
        print(f"❌ Packing List Generation Failed: {result.get('error')}")
    
    return result


if __name__ == "__main__":
    print("\n🚀 Starting Document Generation Tests\n")
    
    # Test all three document types
    bol_result = test_bill_of_lading()
    invoice_result = test_commercial_invoice()
    packing_result = test_packing_list()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    total_tests = 3
    passed = sum([
        bol_result["success"],
        invoice_result["success"],
        packing_result["success"]
    ])
    
    print(f"Tests Passed: {passed}/{total_tests}")
    
    if passed == total_tests:
        print("✅ All document generation tests passed!")
    else:
        print(f"❌ {total_tests - passed} tests failed")
    
    print("\n📁 Generated documents saved in: generated_documents/")
    print("="*60 + "\n")
