# invoice_extractor.py
class InvoiceData:
    """Structure for storing extracted invoice data."""
    
    def __init__(self):
        self.invoice_number = None
        self.invoice_date = None
        self.due_date = None
        self.vendor_name = None
        self.vendor_address = None
        self.billed_to = None
        self.total_amount = None
        self.subtotal = None
        self.tax_amount = None
        self.line_items = []
        self.payment_terms = None
        self.license_info = []
        self.payment_info = {}
        self.currency = None
        self.po_number = None
        self.raw_text = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice data to dictionary."""
        return {
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date,
            'due_date': self.due_date,
            'vendor_name': self.vendor_name,
            'vendor_address': self.vendor_address,
            'billed_to': self.billed_to,
            'total_amount': self.total_amount,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'line_items': self.line_items,
            'payment_terms': self.payment_terms,
            'license_info': self.license_info,
            'payment_info': self.payment_info,
            'currency': self.currency,
            'po_number': self.po_number
        }

class InvoiceExtractor:
    """Extract structured data from invoice text."""
    
    def extract_invoice_data(self, text: str) -> InvoiceData:
        """Extract data from invoice text."""
        invoice = InvoiceData()
        invoice.raw_text = text
        
        # Extract invoice number
        invoice_number_match = re.search(r'invoice\s*(?:#|number|num|no|nbr)[:.\s]*([A-Za-z0-9\-]+)', 
                                         text, re.IGNORECASE)
        if invoice_number_match:
            invoice.invoice_number = invoice_number_match.group(1).strip()
        
        # Extract dates
        date_pattern = r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{2,4}[-/\.]\d{1,2}[-/\.]\d{1,2})'
        invoice_date_match = re.search(
            r'invoice\s*date[:.\s]*' + date_pattern, text, re.IGNORECASE)
        if invoice_date_match:
            invoice.invoice_date = invoice_date_match.group(1).strip()
            
        due_date_match = re.search(
            r'due\s*date[:.\s]*' + date_pattern, text, re.IGNORECASE)
        if due_date_match:
            invoice.due_date = due_date_match.group(1).strip()
        
        # Extract total amount
        amount_pattern = r'[\$€£¥]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)'
        total_match = re.search(
            r'total\s*(?:amount|due)?[:.\s]*' + amount_pattern, text, re.IGNORECASE)
        if total_match:
            invoice.total_amount = total_match.group(1).strip()
            
            # Try to determine currency
            if '$' in total_match.group(0):
                invoice.currency = 'USD'
            elif '€' in total_match.group(0):
                invoice.currency = 'EUR'
            elif '£' in total_match.group(0):
                invoice.currency = 'GBP'
            elif '¥' in total_match.group(0):
                invoice.currency = 'JPY'
        
        # Extract vendor information
        # This is more complex and would require more sophisticated NLP
        # For now, we'll use a simplified approach
        from_section = re.search(r'from[:.\s]*(.*?)\n\n', text, re.IGNORECASE | re.DOTALL)
        if from_section:
            lines = from_section.group(1).strip().split('\n')
            if lines:
                invoice.vendor_name = lines[0].strip()
                invoice.vendor_address = '\n'.join(lines[1:]).strip()
        
        # Extract license information
        license_matches = re.findall(
            r'licen[sc]e\s*(?:number|#|key)?[:.\s]*([A-Za-z0-9\-]+)', 
            text, re.IGNORECASE)
        invoice.license_info = license_matches
        
        # Extract payment information
        payment_method_match = re.search(
            r'payment\s*method[:.\s]*(.*?)\n', text, re.IGNORECASE)
        if payment_method_match:
            invoice.payment_info['method'] = payment_method_match.group(1).strip()
            
        # Look for credit card info (masked)
        cc_match = re.search(r'(?:credit|card).*?([Xx*]{12,15}\d{4})', text)
        if cc_match:
            invoice.payment_info['card'] = cc_match.group(1)
            
        # Extract PO number
        po_match = re.search(r'P\.?O\.?\s*(?:#|number)?[:.\s]*([A-Za-z0-9\-]+)', 
                             text, re.IGNORECASE)
        if po_match:
            invoice.po_number = po_match.group(1).strip()
            
        # Extract payment terms
        terms_match = re.search(r'(?:payment\s*)?terms[:.\s]*(.*?)\n', text, re.IGNORECASE)
        if terms_match:
            invoice.payment_terms = terms_match.group(1).strip()
            
        return invoice
