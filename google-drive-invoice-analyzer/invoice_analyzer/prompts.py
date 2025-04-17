# prompts.py
from typing import Dict, List, Any, Optional
import json

class InvoicePrompts:
    """Prompts for common invoice and vendor management queries."""
    
    @staticmethod
    def vendor_spend_summary(vendor_name: Optional[str] = None) -> str:
        """Prompt for summarizing spend by vendor."""
        if vendor_name:
            return f"""Analyze all invoices from {vendor_name} and provide:
1. Total amount spent
2. Average invoice amount
3. Payment frequency
4. License types purchased
5. Year-over-year spend trends
6. Recommendations for cost optimization"""
        else:
            return """Analyze spending across all vendors and provide:
1. Top 5 vendors by spend
2. Monthly/quarterly spend breakdown
3. Categories of highest expense
4. Year-over-year trends
5. Recommendations for cost optimization"""
    
    @staticmethod
    def license_utilization_analysis() -> str:
        """Prompt for analyzing license utilization."""
        return """Analyze the licenses purchased across all invoices:
1. Total licenses by vendor and type
2. License expiration dates and renewal timeline
3. License cost per user/seat
4. Recommendations for consolidation or optimization
5. License distribution across departments (if applicable)"""
    
    @staticmethod
    def payment_terms_analysis() -> str:
        """Prompt for analyzing payment terms across vendors."""
        return """Analyze payment terms across all vendors:
1. Standard terms by vendor
2. Opportunities for negotiation
3. Early payment discount potential
4. Vendors with inconsistent terms
5. Recommendations for standardization"""
    
    @staticmethod
    def upcoming_payments() -> str:
        """Prompt for generating a list of upcoming payments."""
        return """Generate a schedule of upcoming payments based on invoice due dates:
1. Payments due in the next 30 days
2. Total payment amount by week
3. Vendors with multiple upcoming payments
4. Critical payments to prioritize
5. Recommendations for payment scheduling"""
