import re

import pymupdf


def parse_text_in_area(path, area):
    """
    Get the text from the first page of a PDF file within a specified area.
    """
    with pymupdf.open(path) as doc:
        if doc.page_count == 0:
            return None

        page = doc[0]
        area = get_area(page.rect.width, page.rect.height, area)

        tp = page.get_textpage(clip=area)
        text = tp.extractText()

        if not text:
            return None

        text = re.sub(r" {2,}", " ", text).strip()
        return text


def parse_table(
    path,
    columns=[],
    page_area=[0, 0, -1, -1],
    first_page_area=None,
    pages=None,
    required_columns=[],
    multiple_page_rows=[],
    stop_fn=None,
):
    """
    Parses a PDF file and extracts text values from specified columns within a given area.
    Args:
        path (str): The path to the PDF file.
        columns (dict): A dictionary mapping column names to their x-coordinate ranges.
        page_area (list): A list representing the area of the page to search for text values. Format: [x1, y1, x2, y2].
        first_page_area (list): A list representing the area of the first page to search for text values. Format: [x1, y1, x2, y2].
        pages (list or number): A list representing the range of pages to parse. Format: [start_page, end_page].
        required_columns (list): A list of column names that must be present in each extracted value.
        multiple_page_rows (list): A list of column names that, if present together, indicate a possible multiple-row value.
        stop_fn (function): A function that takes a current value and list of extracted values and returns True if the parsing should stop.
    Returns:
        list: A list of dictionaries, where each dictionary represents a row of extracted values. The keys of the dictionaries are the column names, and the values are the extracted text values.
    """
    values = []
    with pymupdf.open(path) as doc:
        pages = (
            [1, -1]
            if pages is None
            else ([pages, -1] if isinstance(pages, int) else pages)
        )
        pages[0] = pages[0] if pages[0] != -1 else doc.page_count
        pages[1] = pages[1] if pages[1] != -1 else doc.page_count
        if len(required_columns) == 0:
            required_columns = columns.keys()
        # Iterate through the pages of the PDF
        for page_num, page in enumerate(doc):
            page_num += 1
            if page_num < pages[0] or page_num > pages[1]:
                continue

            area = get_area(
                page.rect.width,
                page.rect.height,
                (first_page_area if page_num == 1 and first_page_area else page_area),
            )

            page_data = page.get_text("dict", clip=area)
            # Iterate through the blocks of text in the page
            for block in page_data["blocks"]:
                if "lines" not in block:
                    continue

                value = {}
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        bbox = span["bbox"]

                        x = bbox[2]
                        for key, (x1, x2) in columns.items():
                            if x >= x1 and x <= x2 and text != "":
                                if key not in value:
                                    value[key] = ""
                                value[key] += " " + text
                                value[key] = value[key].strip()

                is_multiple_page_rows = (
                    len(multiple_page_rows) > 0
                    and list(value.keys()) == multiple_page_rows
                )

                # validation
                if (
                    not all(k in value for k in required_columns)
                    and not is_multiple_page_rows
                ):
                    continue
                # Add "multiple_page_rows" values to the last row
                if is_multiple_page_rows:
                    if len(values) == 0:
                        continue
                    # Merge with the last value in values
                    last_index = len(values) - 1
                    last_value = values[last_index]
                    for k in multiple_page_rows:
                        last_value[k] += " " + value[k]
                        last_value[k] = last_value[k].strip()
                    values[last_index] = last_value
                else:
                    # add empty values for missing columns
                    for k in columns.keys():
                        if k not in value:
                            value[k] = ""
                        value[k] = value[k].strip()
                    values.append(value)
                    if stop_fn and stop_fn(value, values):
                        break
    return values


def get_area(page_width, page_height, area):
    area = list(area)
    area[0] = area[0] if area[0] != -1 else page_width
    area[1] = area[1] if area[1] != -1 else page_height
    area[2] = area[2] if area[2] != -1 else page_width
    area[3] = area[3] if area[3] != -1 else page_height

    return pymupdf.Rect(area)
