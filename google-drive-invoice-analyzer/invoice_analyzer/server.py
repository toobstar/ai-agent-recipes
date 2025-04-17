# server.py
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context
from gdrive import GoogleDriveClient
from pdf_processor import PDFProcessor
from invoice_extractor import InvoiceExtractor
from prompts import InvoicePrompts

# Initialize our MCP server
mcp = FastMCP("Google Drive Invoice Analyzer")

# Initialize our components
drive_client = GoogleDriveClient()
pdf_processor = PDFProcessor()
invoice_extractor = InvoiceExtractor()

# Data storage
invoice_data_dir = Path("invoice_data")
invoice_data_dir.mkdir(exist_ok=True)
processed_files = set()
invoice_database = {}

# Google Drive folder ID to monitor
FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "")

# Database management
def save_invoice_data(invoice_id: str, data: Dict[str, Any]):
    """Save extracted invoice data to file system."""
    file_path = invoice_data_dir / f"{invoice_id}.json"
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    invoice_database[invoice_id] = data
    
def load_invoice_database():
    """Load all processed invoices into memory."""
    global invoice_database
    for file_path in invoice_data_dir.glob("*.json"):
        with open(file_path, "r") as f:
            data = json.load(f)
            invoice_id = file_path.stem
            invoice_database[invoice_id] = data

# Process new files from Google Drive
def handle_new_files(files: List[Dict[str, Any]]):
    """Process new files detected in Google Drive."""
    for file_info in files:
        file_id = file_info["id"]
        
        # Skip already processed files
        if file_id in processed_files:
            continue
            
        # Only process PDFs
        if not drive_client.is_pdf(file_info):
            continue
            
        # Download the file
        file_data = drive_client.download_file(file_id)
        
        # Extract text from PDF
        text = pdf_processor.extract_text(file_data)
        
        # Check if it's an invoice
        if pdf_processor.is_invoice(text):
            # Extract invoice data
            invoice_data = invoice_extractor.extract_invoice_data(text)
            
            # Generate an invoice ID if one isn't found
            invoice_id = invoice_data.invoice_number or f"inv_{file_id}"
            
            # Save the extracted data
            save_invoice_data(invoice_id, invoice_data.to_dict())
            
            # Add raw text to metadata for context
            metadata = {
                "raw_text": text,
                "file_name": file_info["name"],
                "file_id": file_id,
                "processed_date": datetime.now().isoformat()
            }
            
            # Save metadata
            metadata_path = invoice_data_dir / f"{invoice_id}_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
                
        # Mark as processed
        processed_files.add(file_id)

# MCP Resource - Get list of invoices
@mcp.resource("invoices://list")
def list_invoices() -> str:
    """List all processed invoices."""
    invoices = []
    for invoice_id, data in invoice_database.items():
        invoice_summary = {
            "id": invoice_id,
            "vendor": data.get("vendor_name", "Unknown"),
            "date": data.get("invoice_date", "Unknown"),
            "amount": data.get("total_amount", "Unknown"),
            "currency": data.get("currency", "USD")
        }
        invoices.append(invoice_summary)
        
    return json.dumps(invoices, indent=2)

# MCP Resource - Get specific invoice
@mcp.resource("invoices://{invoice_id}")
def get_invoice(invoice_id: str) -> str:
    """Get details for a specific invoice."""
    if invoice_id in invoice_database:
        return json.dumps(invoice_database[invoice_id], indent=2)
    else:
        return json.dumps({"error": "Invoice not found"})

# MCP Resource - Get vendor list
@mcp.resource("vendors://list")
def list_vendors() -> str:
    """List all vendors from processed invoices."""
    vendors = {}
    for invoice_id, data in invoice_database.items():
        vendor_name = data.get("vendor_name")
        if vendor_name:
            if vendor_name not in vendors:
                vendors[vendor_name] = {
                    "invoice_count": 0,
                    "total_spend": 0
                }
            vendors[vendor_name]["invoice_count"] += 1
            
            # Add to total if amount is available
            amount = data.get("total_amount")
            if amount and isinstance(amount, (int, float, str)):
                try:
                    amount = float(str(amount).replace(",", ""))
                    vendors[vendor_name]["total_spend"] += amount
                except ValueError:
                    pass
    
    return json.dumps(list(vendors.keys()), indent=2)

# MCP Resource - Get specific vendor details
@mcp.resource("vendors://{vendor_name}")
def get_vendor(vendor_name: str) -> str:
    """Get details for a specific vendor."""
    vendor_invoices = []
    for invoice_id, data in invoice_database.items():
        if data.get("vendor_name") == vendor_name:
            vendor_invoices.append({
                "id": invoice_id,
                "date": data.get("invoice_date"),
                "amount": data.get("total_amount"),
                "currency": data.get("currency", "USD")
            })
    
    return json.dumps(vendor_invoices, indent=2)

# MCP Tool - Start monitoring Google Drive folder
@mcp.tool()
def start_monitoring(folder_id: Optional[str] = None) -> str:
    """
    Start monitoring a Google Drive folder for new invoice PDFs.
    
    Args:
        folder_id: The Google Drive folder ID to monitor (optional)
    """
    target_folder = folder_id or FOLDER_ID
    if not target_folder:
        return "No folder ID provided. Please specify a folder ID or set the GDRIVE_FOLDER_ID environment variable."
    
    drive_client.start_watching_folder(target_folder, handle_new_files)
    return f"Started monitoring folder with ID: {target_folder}"

# MCP Tool - Process a specific Google Drive file
@mcp.tool()
def process_file(file_id: str) -> str:
    """
    Process a specific file from Google Drive.
    
    Args:
        file_id: The Google Drive file ID to process
    """
    try:
        # Get file info
        file_info = drive_client.service.files().get(
            fileId=file_id, fields="id,name,mimeType").execute()
        
        # Check if it's a PDF
        if not drive_client.is_pdf(file_info):
            return "This file is not a PDF."
        
        # Download and process
        file_data = drive_client.download_file(file_id)
        text = pdf_processor.extract_text(file_data)
        
        if not pdf_processor.is_invoice(text):
            return "This PDF does not appear to be an invoice."
        
        # Extract invoice data
        invoice_data = invoice_extractor.extract_invoice_data(text)
        
        # Generate an invoice ID if one isn't found
        invoice_id = invoice_data.invoice_number or f"inv_{file_id}"
        
        # Save the extracted data
        save_invoice_data(invoice_id, invoice_data.to_dict())
        
        # Add to processed set
        processed_files.add(file_id)
        
        return f"Successfully processed invoice {invoice_id} from file {file_info['name']}"
        
    except Exception as e:
        return f"Error processing file: {str(e)}"

# MCP Tool - Get invoice analytics
@mcp.tool()
def get_invoice_analytics() -> str:
    """
    Get analytics on all processed invoices.
    """
    if not invoice_database:
        return "No invoices have been processed yet."
    
    total_invoices = len(invoice_database)
    vendors = set()
    total_amount = 0
    currencies = {}
    earliest_date = None
    latest_date = None
    
    for invoice_id, data in invoice_database.items():
        # Count vendors
        if data.get("vendor_name"):
            vendors.add(data.get("vendor_name"))
        
        # Sum amounts
        amount = data.get("total_amount")
        currency = data.get("currency", "Unknown")
        
        if amount and isinstance(amount, (int, float, str)):
            try:
                amount = float(str(amount).replace(",", ""))
                total_amount += amount
                
                if currency not in currencies:
                    currencies[currency] = 0
                currencies[currency] += amount
            except ValueError:
                pass
        
        # Track date range
        date = data.get("invoice_date")
        if date:
            try:
                # Simplified date parsing - would need more robust handling
                parsed_date = datetime.strptime(date, "%m/%d/%Y")
                if not earliest_date or parsed_date < earliest_date:
                    earliest_date = parsed_date
                if not latest_date or parsed_date > latest_date:
                    latest_date = parsed_date
            except ValueError:
                pass
    
    # Format results
    analytics = {
        "total_invoices": total_invoices,
        "vendor_count": len(vendors),
        "vendor_list": list(vendors),
        "total_amount_by_currency": currencies,
        "date_range": {
            "earliest": earliest_date.strftime("%Y-%m-%d") if earliest_date else "Unknown",
            "latest": latest_date.strftime("%Y-%m-%d") if latest_date else "Unknown"
        }
    }
    
    return json.dumps(analytics, indent=2)

# MCP Tool - Search invoices by criteria
@mcp.tool()
def search_invoices(
    vendor: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None
) -> str:
    """
    Search invoices by various criteria.
    
    Args:
        vendor: Filter by vendor name (optional)
        min_amount: Filter by minimum amount (optional)
        max_amount: Filter by maximum amount (optional)
        start_date: Filter by start date (MM/DD/YYYY) (optional)
        end_date: Filter by end date (MM/DD/YYYY) (optional)
        keyword: Search invoice text for keyword (optional)
    """
    matches = []
    
    for invoice_id, data in invoice_database.items():
        # Initialize as a match
        is_match = True
        
        # Check vendor
        if vendor and data.get("vendor_name") != vendor:
            is_match = False
            
        # Check amount range
        amount = data.get("total_amount")
        if amount and (min_amount is not None or max_amount is not None):
            try:
                amount_float = float(str(amount).replace(",", ""))
                
                if min_amount is not None and amount_float < min_amount:
                    is_match = False
                    
                if max_amount is not None and amount_float > max_amount:
                    is_match = False
            except ValueError:
                # If we can't parse the amount, it doesn't match numeric filters
                if min_amount is not None or max_amount is not None:
                    is_match = False
        
        # Check date range
        invoice_date = data.get("invoice_date")
        if invoice_date and (start_date or end_date):
            try:
                date_obj = datetime.strptime(invoice_date, "%m/%d/%Y")
                
                if start_date:
                    start = datetime.strptime(start_date, "%m/%d/%Y")
                    if date_obj < start:
                        is_match = False
                        
                if end_date:
                    end = datetime.strptime(end_date, "%m/%d/%Y")
                    if date_obj > end:
                        is_match = False
            except ValueError:
                # If we can't parse the date, it doesn't match date filters
                if start_date or end_date:
                    is_match = False
        
        # Check keyword in raw text
        if keyword:
            # Load metadata to get raw text
            metadata_path = invoice_data_dir / f"{invoice_id}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    raw_text = metadata.get("raw_text", "").lower()
                    
                    if keyword.lower() not in raw_text:
                        is_match = False
            else:
                # If no metadata with raw text, can't match keyword
                is_match = False
        
        # Add to results if all criteria match
        if is_match:
            matches.append({
                "id": invoice_id,
                "vendor": data.get("vendor_name", "Unknown"),
                "date": data.get("invoice_date", "Unknown"),
                "amount": data.get("total_amount", "Unknown"),
                "currency": data.get("currency", "USD")
            })
    
    return json.dumps(matches, indent=2)

# MCP Prompts
@mcp.prompt()
def vendor_spend_summary(vendor_name: Optional[str] = None) -> str:
    """
    Generate a summary of spending by vendor.
    
    Args:
        vendor_name: Optional specific vendor to analyze
    """
    return InvoicePrompts.vendor_spend_summary(vendor_name)

@mcp.prompt()
def license_utilization_analysis() -> str:
    """
    Analyze license utilization across all invoices.
    """
    return InvoicePrompts.license_utilization_analysis()

@mcp.prompt()
def payment_terms_analysis() -> str:
    """
    Analyze payment terms across vendors.
    """
    return InvoicePrompts.payment_terms_analysis()

@mcp.prompt()
def upcoming_payments() -> str:
    """
    Generate a schedule of upcoming payments.
    """
    return InvoicePrompts.upcoming_payments()

# Initialize the database on startup
load_invoice_database()

# Start the server
if __name__ == "__main__":
    mcp.run()
