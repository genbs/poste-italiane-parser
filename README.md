# Poste Italiane Documents Parser

_agli sventurati che hanno un conto postale_

A Python tool to parse PDF documents from Poste Italiane and convert them into structured JSON or CSV data. It automatically identifies the document type and validates financial data to ensure integrity.

---

## Key Features

- **Automatic Document Detection**: Identifies the document type (e.g., BancoPosta statement, Postepay report) from the PDF content.
- **Data Validation**: Performs validation checks on account statements to ensure balances and totals match the transactional data.
- **Multiple Output Formats**: Export extracted data to JSON (default) or CSV formats.
- **Batch Processing**: Analyze a single PDF or an entire directory of documents at once.

---

## Supported Documents

- Estratto Conto BancoPosta
- Rendiconto Postepay Evolution
- Lista Movimenti Postepay Evolution

---

## Installation

1.  Clone the repository:

```bash
git clone https://github.com/genbs/poste-italiane-parser.git
cd poste-italiane-parser
```

2.  Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Download the documents you wish to analyze from your Poste Italiane online account, then run the script from your terminal.
You can download the document from [here](https://comunicazionionline.poste.it/tbr/routes/l1/documenti)

### Arguments

- `-p`, `--path` (Required): Path to the PDF file or a directory containing PDF files.
- `-f`, `--format` (Optional): Output format (`json` or `csv`). Defaults to `json`.
- `-o`, `--output` (Optional): Path for the output file or directory. By default, output is saved to the same directory as the input.
- `-v`, `--verbose` (Optional): Enable verbose logging for debugging purposes.

### Examples

```bash
# Extract data from a single PDF to a JSON file
python main.py --path "path/to/documents/statement.pdf"

# Extract data from a single PDF to CSV, specifying an output file
python main.py --path "path/to/documents/postepay_report.pdf" --format csv --output "output/report_data.csv"

# Extract data from all PDFs in a directory and save to an output folder
python main.py "path/to/documents/" -o "out/"
```

---

## Using as a Library

You can also import and use the parser directly in your Python projects.

**Install the package:**

```bash
pip install poste_italiane_parser
```

**Use it in your script:**

```python
from poste_italiane_parser import PosteItalianeParser

file_path = "path/to/your/statement.pdf"

try:
    data = PosteItalianeParser(file_path)
    # Print some of the extracted data
    print(f"Document Type: {data['document_type']}")
    print(f"Holder: {data['holder']}")
    print(f"Final Balance: {data['final_balance']}")

except ValueError as e:
    print(f"Error: {e}")
except FileNotFoundError:
    print(f"Error: The file was not found at {file_path}")

```

---

## Output Format

The result of parsing

```json
  {
    "generated_at": "string | null",
    "document_type": "ESTRATTO_CONTO | LISTA_MOVIMENTI | RENDICONTO",
    "currency": "string",
    "initial_balance": "float | null",
    "final_balance": "float | null",
    "iban": "string | null",
    "holder": "string",
    "card_number": "string | null",
    "account_number": "string | null",
    "period": {
        "start_date": "string",
        "end_date": "string"
    },
    "customer": {
        "name": "string",
        "street": "string | null",
        "city": "string | null",
    },
    "transactions": [
        {
            "accounting_date": "string",
            "value_date": "string",
            "description": "string",
            "debits": "float",
            "credits": "float",
            "value": "float"
        }[]
    ]
}
```

**Note:** Dates are formatted as YYYY-MM-DD HH:MM:SS, and all monetary values are floats.

## Testing

This repository does not include test PDFs to avoid committing sensitive personal data. Instead, tests are designed to run against result files.

To run the test suite, you must first create a `[my-test-name].test.json` file for each test case. This file is json formatted and should contain the expected output structure. Here is an example of how to structure your test result file:

```json
{
	"path": "tests/xxx.pdf",
	"currency": "EURO",
	"generated_at": "xxx",
	"account_number": "xxxx",
	"period_start_date": "xxx",
	"period_end_date": "xxx",
	"holder": "xxx xxx",
	"customer_name": "xxx xxx",
	"customer_street": "xxx",
	"customer_city": "xxx",
	"initial_balance": 0,
	"final_balance": 0,
	"card_number": "",
	"iban": "xxxx",
	"transactions": [
		{
			"accounting_date": "xxx",
			"value_date": "xxx",
			"description": "xxx",
			"credits": 0,
			"debits": 0
		}
	]
}
```

For the transactions, you can include all expected ones or just a subset.

Once your test result files are set up, run the tests with the verbose flag:

```bash
python -m unittest tests/test_PosteItalianeParser.py -v
```

## Contributing

Contributions are welcome. Please feel free to submit a pull request or open an issue for bugs, feature requests, or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
