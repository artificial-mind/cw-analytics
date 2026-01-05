"""
Document Generator Service - Using ReportLab
Generates logistics documents (BOL, Invoice, Packing List) as PDFs
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image, Frame, PageTemplate
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

logger = logging.getLogger(__name__)


class DocumentGeneratorReportLab:
    """Generate logistics documents using ReportLab."""
    
    def __init__(self):
        """Initialize the document generator."""
        self.output_dir = Path(__file__).parent.parent.parent / "generated_documents"
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info(f"DocumentGenerator initialized. Output: {self.output_dir}")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoValue',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica'
        ))
    
    def generate_bill_of_lading(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a Bill of Lading PDF using ReportLab.
        
        Args:
            data: Dictionary containing BOL data
        
        Returns:
            dict with success, file_path, document_url, error
        """
        try:
            logger.info(f"Generating Bill of Lading for shipment {data.get('shipment_id')}")
            
            # Prepare data
            data['generation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['document_number'] = data.get('document_number', f"BOL-{data['shipment_id']}")
            data['issue_date'] = data.get('issue_date', datetime.now().strftime("%Y-%m-%d"))
            
            # Set defaults
            data.setdefault('bol_type', 'ORIGINAL')
            data.setdefault('carrier_address', 'Address not provided')
            data.setdefault('booking_number', 'N/A')
            
            # Calculate totals
            if 'containers' in data:
                data['total_containers'] = len(data['containers'])
                data['total_packages'] = sum(c.get('package_count', 0) for c in data['containers'])
                data['total_weight'] = sum(c.get('weight', 0) for c in data['containers'])
                data['total_volume'] = sum(c.get('volume', 0) for c in data['containers'])
            
            # Create PDF
            filename = f"BOL_{data['shipment_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = self.output_dir / filename
            
            doc = SimpleDocTemplate(str(file_path), pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
            
            story = []
            
            # Title
            story.append(Paragraph("BILL OF LADING", self.styles['DocumentTitle']))
            story.append(Paragraph(f"B/L Number: {data['document_number']}", self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Carrier Info
            carrier_data = [[Paragraph(f"<b>Carrier:</b> {data['carrier_name']}", self.styles['Normal'])]]
            carrier_data.append([Paragraph(f"<b>Booking:</b> {data.get('booking_number', 'N/A')}", self.styles['Normal'])])
            carrier_data.append([Paragraph(f"<b>Issue Date:</b> {data['issue_date']}", self.styles['Normal'])])
            
            carrier_table = Table(carrier_data, colWidths=[17*cm])
            carrier_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(carrier_table)
            story.append(Spacer(1, 12))
            
            # Shipper/Consignee
            party_data = [
                [Paragraph("<b>Shipper</b>", self.styles['InfoLabel']),
                 Paragraph("<b>Consignee</b>", self.styles['InfoLabel'])],
                [Paragraph(f"{data['shipper_name']}<br/>{data['shipper_address']}<br/>{data['shipper_city']}, {data['shipper_country']}", self.styles['Normal']),
                 Paragraph(f"{data['consignee_name']}<br/>{data['consignee_address']}<br/>{data['consignee_city']}, {data['consignee_country']}", self.styles['Normal'])]
            ]
            
            party_table = Table(party_data, colWidths=[8.5*cm, 8.5*cm])
            party_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(party_table)
            story.append(Spacer(1, 12))
            
            # Vessel Info
            story.append(Paragraph("Vessel & Voyage Information", self.styles['SectionTitle']))
            vessel_data = [
                ["Vessel Name", data['vessel_name'], "Voyage Number", data.get('voyage_number', 'N/A')],
                ["Port of Loading", data['port_of_loading'], "Port of Discharge", data['port_of_discharge']]
            ]
            
            vessel_table = Table(vessel_data, colWidths=[4.25*cm, 4.25*cm, 4.25*cm, 4.25*cm])
            vessel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold')
            ]))
            story.append(vessel_table)
            story.append(Spacer(1, 12))
            
            # Container Details
            story.append(Paragraph("Container & Cargo Details", self.styles['SectionTitle']))
            container_headers = ["Container No.", "Seal No.", "Type", "Packages", "Weight (KG)", "Volume (CBM)"]
            container_data = [container_headers]
            
            for container in data.get('containers', []):
                container_data.append([
                    container.get('number', 'N/A'),
                    container.get('seal_number', 'N/A'),
                    container.get('type', 'N/A'),
                    f"{container.get('package_count', 0)} {container.get('package_type', 'PCS')}",
                    str(container.get('weight', 0)),
                    str(container.get('volume', 0))
                ])
            
            container_table = Table(container_data, colWidths=[4*cm, 2.5*cm, 2*cm, 3*cm, 2.5*cm, 3*cm])
            container_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
            ]))
            story.append(container_table)
            story.append(Spacer(1, 12))
            
            # Totals
            totals_text = f"<b>Total Containers:</b> {data.get('total_containers', 0)} | <b>Total Packages:</b> {data.get('total_packages', 0)} | <b>Total Weight:</b> {data.get('total_weight', 0)} KG"
            story.append(Paragraph(totals_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"BOL generated successfully: {file_path}")
            
            return {
                "success": True,
                "document_type": "BILL_OF_LADING",
                "document_number": data['document_number'],
                "file_path": str(file_path),
                "document_url": f"/documents/{filename}",
                "file_size_kb": round(file_path.stat().st_size / 1024, 2)
            }
            
        except Exception as e:
            logger.error(f"Error generating BOL: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_commercial_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a Commercial Invoice PDF."""
        try:
            logger.info(f"Generating Commercial Invoice {data.get('invoice_number')}")
            
            # Prepare data
            data['generation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['invoice_date'] = data.get('invoice_date', datetime.now().strftime("%Y-%m-%d"))
            data['currency'] = data.get('currency', 'USD')
            
            # Calculate totals
            if 'line_items' in data:
                for item in data['line_items']:
                    item['total_value'] = item['quantity'] * item['unit_price']
                
                subtotal = sum(item['total_value'] for item in data['line_items'])
                data['subtotal'] = subtotal
                data['discount_amount'] = (subtotal * data.get('discount_percentage', 0)) / 100
                freight = data.get('freight_charges', 0)
                insurance = data.get('insurance_charges', 0)
                vat_amt = ((subtotal - data['discount_amount'] + freight + insurance) * data.get('vat_percentage', 0)) / 100
                data['vat_amount'] = vat_amt
                data['grand_total'] = subtotal - data['discount_amount'] + freight + insurance + vat_amt
            
            # Create PDF
            filename = f"INV_{data['invoice_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = self.output_dir / filename
            
            doc = SimpleDocTemplate(str(file_path), pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
            
            story = []
            
            # Title
            story.append(Paragraph("COMMERCIAL INVOICE", self.styles['DocumentTitle']))
            story.append(Paragraph(f"Invoice #{data['invoice_number']} | Date: {data['invoice_date']}", self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Exporter/Importer
            party_data = [
                [Paragraph("<b>Exporter (Seller)</b>", self.styles['InfoLabel']),
                 Paragraph("<b>Importer (Buyer)</b>", self.styles['InfoLabel'])],
                [Paragraph(f"{data['exporter_name']}<br/>{data['exporter_address']}<br/>{data['exporter_city']}, {data['exporter_country']}", self.styles['Normal']),
                 Paragraph(f"{data['importer_name']}<br/>{data['importer_address']}<br/>{data['importer_city']}, {data['importer_country']}", self.styles['Normal'])]
            ]
            
            party_table = Table(party_data, colWidths=[8.5*cm, 8.5*cm])
            party_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(party_table)
            story.append(Spacer(1, 12))
            
            # Line Items
            story.append(Paragraph("Invoice Line Items", self.styles['SectionTitle']))
            item_headers = ["Item", "Description", "HS Code", "Qty", "Unit Price", "Total"]
            item_data = [item_headers]
            
            for idx, item in enumerate(data.get('line_items', []), 1):
                item_data.append([
                    str(idx),
                    item['description'],
                    item['hs_code'],
                    str(item['quantity']),
                    f"${item['unit_price']:.2f}",
                    f"${item['total_value']:.2f}"
                ])
            
            item_table = Table(item_data, colWidths=[1*cm, 6*cm, 2.5*cm, 1.5*cm, 3*cm, 3*cm])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
            ]))
            story.append(item_table)
            story.append(Spacer(1, 12))
            
            # Totals
            totals_data = [
                ["Subtotal:", f"${data['subtotal']:.2f}"],
                ["Freight:", f"${data.get('freight_charges', 0):.2f}"],
                ["Insurance:", f"${data.get('insurance_charges', 0):.2f}"],
                ["<b>GRAND TOTAL:</b>", f"<b>${data['grand_total']:.2f}</b>"]
            ]
            
            totals_table = Table(totals_data, colWidths=[12*cm, 5*cm])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black)
            ]))
            story.append(totals_table)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Commercial Invoice generated: {file_path}")
            
            return {
                "success": True,
                "document_type": "COMMERCIAL_INVOICE",
                "invoice_number": data['invoice_number'],
                "file_path": str(file_path),
                "document_url": f"/documents/{filename}",
                "file_size_kb": round(file_path.stat().st_size / 1024, 2),
                "total_amount": data['grand_total'],
                "currency": data['currency']
            }
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_packing_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a Packing List PDF."""
        try:
            logger.info(f"Generating Packing List {data.get('packing_list_number')}")
            
            # Prepare data
            data['generation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['issue_date'] = data.get('issue_date', datetime.now().strftime("%Y-%m-%d"))
            
            # Calculate totals
            if 'packages' in data:
                data['total_packages'] = len(data['packages'])
                data['total_gross_weight'] = sum(p.get('gross_weight', 0) for p in data['packages'])
                data['total_net_weight'] = sum(p.get('net_weight', 0) for p in data['packages'])
                data['total_volume'] = sum(p.get('volume', 0) for p in data['packages'])
            
            # Create PDF
            filename = f"PKG_{data['packing_list_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = self.output_dir / filename
            
            doc = SimpleDocTemplate(str(file_path), pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
            
            story = []
            
            # Title
            story.append(Paragraph("PACKING LIST", self.styles['DocumentTitle']))
            story.append(Paragraph(f"Packing List #{data['packing_list_number']}", self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Shipper/Consignee
            party_data = [
                ["Shipper", "Consignee"],
                [f"{data['shipper_name']}\n{data['shipper_address']}\n{data['shipper_city']}, {data['shipper_country']}",
                 f"{data['consignee_name']}\n{data['consignee_address']}\n{data['consignee_city']}, {data['consignee_country']}"]
            ]
            
            party_table = Table(party_data, colWidths=[8.5*cm, 8.5*cm])
            party_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(party_table)
            story.append(Spacer(1, 12))
            
            # Package summaries
            for idx, pkg in enumerate(data.get('packages', []), 1):
                story.append(Paragraph(f"Package {idx} of {data['total_packages']} - {pkg['package_type']}", self.styles['SectionTitle']))
                
                pkg_info = [
                    ["Package ID:", pkg['package_id'], "Gross Weight:", f"{pkg['gross_weight']} KG"],
                    ["Dimensions:", f"{pkg['length']}x{pkg['width']}x{pkg['height']} cm", "Net Weight:", f"{pkg['net_weight']} KG"]
                ]
                
                pkg_table = Table(pkg_info, colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
                pkg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('BORDER', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                story.append(pkg_table)
                story.append(Spacer(1, 8))
            
            # Totals
            story.append(Paragraph("Shipment Summary", self.styles['SectionTitle']))
            totals_text = f"<b>Total Packages:</b> {data['total_packages']} | <b>Gross Weight:</b> {data['total_gross_weight']:.2f} KG | <b>Volume:</b> {data['total_volume']:.4f} CBM"
            story.append(Paragraph(totals_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Packing List generated: {file_path}")
            
            return {
                "success": True,
                "document_type": "PACKING_LIST",
                "packing_list_number": data['packing_list_number'],
                "file_path": str(file_path),
                "document_url": f"/documents/{filename}",
                "file_size_kb": round(file_path.stat().st_size / 1024, 2),
                "total_packages": data['total_packages'],
                "total_weight_kg": data['total_gross_weight']
            }
            
        except Exception as e:
            logger.error(f"Error generating packing list: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_generator = None

def get_document_generator() -> DocumentGeneratorReportLab:
    """Get or create the document generator instance."""
    global _generator
    if _generator is None:
        _generator = DocumentGeneratorReportLab()
    return _generator
