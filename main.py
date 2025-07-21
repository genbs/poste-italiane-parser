import argparse
import csv
import json
import logging
import os

from poste_italiane_parser import PosteItalianeParser


def parse_args():
    parser = argparse.ArgumentParser(description="Parse PDF files from Poste Italiane.")
    parser.add_argument("path", type=str, help="Path to the files to parse.")
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["json", "csv"],
        help="Output format (default: from output extension or json). The CSV format exports only transactions. ",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path or directory (optional). If not specified, output will be to a file with the same name as the input file with the specified format.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging."
    )

    return parser.parse_args()


def get_output_filename(path, output, format):
    """
    Get the output filename based on the input path, output parameter, and format.
    """
    if not output:
        base_name_without_ext = os.path.splitext(path)[0]
        return f"{base_name_without_ext}.{format}"

    if os.path.isdir(output) or not os.path.splitext(output)[1]:
        base_name_without_ext = os.path.splitext(os.path.basename(path))[0]
        output_filename = os.path.join(output, f"{base_name_without_ext}.{format}")
    else:
        output_filename = output

    # check if output directory exists, if not create it
    output_dir = os.path.dirname(output_filename)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return output_filename


def save(data, format, output_filename):
    """
    Save the parsed data to a file in the specified format.
    """
    if format == "json":
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    elif format == "csv":
        # export only transactions
        data = data["transactions"]
        with open(output_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())
    else:
        raise ValueError("Unsupported format: {}".format(format))


def is_valid_pdf(path):
    """
    Check if the given path is a valid PDF file.
    """
    return os.path.isfile(path) and path.lower().endswith(".pdf")


def main(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # check if the path is a PDF file or directory
    if os.path.isdir(args.path):
        paths = [
            os.path.join(args.path, f)
            for f in os.listdir(args.path)
            if is_valid_pdf(os.path.join(args.path, f))
        ]
    elif is_valid_pdf(args.path):
        paths = [args.path]
    else:
        raise ValueError(f"Invalid path or no valid PDF files found in {args.path}")

    # determine output format
    output_format = (
        args.format
        if args.format
        else ("json" if not args.output or not args.output.endswith(".csv") else "csv")
    )

    for path in paths:
        logging.debug(f"Processing file: {path}")

        try:
            data = PosteItalianeParser(path)
            if not data:
                logging.warning(f"No data found in file: {path}")
                continue
        except Exception as e:
            logging.error(f"Error parsing file {path}: {e}")
            if args.debug:
                raise

            continue

        # Save the parsed data
        try:
            output_filename = get_output_filename(path, args.output, output_format)
            save(data, output_format, output_filename)
            logging.info(f"Data written to {output_filename}")

        except Exception as e:
            logging.error(f"Error saving data for file {path}: {e}")
            continue


if __name__ == "__main__":
    args = parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

        if args.verbose:
            import traceback

            traceback.print_exc()
