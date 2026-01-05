"""
CW Analytics Engine - Document Generation Module
"""

from .generator_reportlab import DocumentGeneratorReportLab as DocumentGenerator, get_document_generator

__all__ = ['DocumentGenerator', 'get_document_generator']
