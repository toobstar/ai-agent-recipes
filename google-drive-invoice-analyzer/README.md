# Google Drive Invoice Analyzer MCP Server

An MCP server that monitors Google Shared Drive folders for PDF invoices, extracts licensing and payment information, and provides tools for vendor and cost management analysis.

## Features

- **Google Drive Integration**: Monitor shared folders for new PDF files
- **Automatic Invoice Detection**: Identify PDFs that contain invoice data
- **Data Extraction**: Extract key information including vendor details, payment terms, and licensing info
- **Analytics Tools**: Generate insights on spending patterns and vendor relationships
- **Common Prompts**: Ready-to-use prompts for vendor/cost management questions

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Drive API enabled
- OAuth 2.0 credentials for Google Drive API

## Installation

1. Clone this repository:
git clone <repository-url>
cd google-drive-invoice-analyzer

2. Install dependencies:
pip install -r requirements.txt

3. Set up Google Drive authentication:
- Go to the [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select an existing project
- Enable the Google Drive API
- Create OAuth 2.0 Client ID credentials (Desktop application)
- Download the credentials JSON file
- Rename it to `credentials.json` and place it in the project root directory

## Configuration

Create a `.env` file in the project root with the following variables:
GDRIVE_FOLDER_ID=<your-google-drive-folder-id>

You can find the folder ID in the URL when you open the folder in Google Drive:
`https://drive.google.com/drive/folders/<folder-id>`

## Usage

### Run the MCP Server
python -m invoice_analyzer.server

On first run, you'll be prompted to authorize the application to access your Google Drive.

### Connect to Claude Desktop

1. Open Claude Desktop settings
2. Edit Config to add the MCP server:

```json
{
  "mcpServers": {
    "invoice-analyzer": {
      "command": "python",
      "args": ["-m", "invoice_analyzer.server"]
    }
  }
}

Restart Claude Desktop

Available Resources

invoices://list - List all processed invoices
invoices://{invoice_id} - Get details for a specific invoice
vendors://list - List all vendors from processed invoices
vendors://{vendor_name} - Get details for a specific vendor

Available Tools

start_monitoring - Start monitoring a Google Drive folder for new invoice PDFs
process_file - Process a specific file from Google Drive
get_invoice_analytics - Get analytics on all processed invoices
search_invoices - Search invoices by various criteria (vendor, amount, date, etc.)

Available Prompts

vendor_spend_summary - Generate a summary of spending by vendor
license_utilization_analysis - Analyze license utilization across all invoices
payment_terms_analysis - Analyze payment terms across vendors
upcoming_payments - Generate a schedule of upcoming payments

Data Storage
Extracted invoice data is stored in the invoice_data directory as JSON files.
Limitations

Currently optimized for English-language invoices
PDF text extraction may vary in quality depending on PDF structure
Date format parsing uses MM/DD/YYYY format
