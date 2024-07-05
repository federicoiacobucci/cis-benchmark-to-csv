#!/usr/bin/env python3

import argparse
import csv
import re
import pdfplumber
import sys

# Updated regular expression to match recommendation lines more flexibly
recommendation_pattern = re.compile(r'^(\d+\.\d+)\s+\((L\d+)\)\s+(.+?)(?:\s+\(Manual\)|\s+\(Automated\))?(?:\s*\.+\s*\d+)?$', re.IGNORECASE)


fields = [
    'Description',
    'Rationale',
    'Impact',
    'Audit',
    'Remediation',
    'Default Value',
    'References',
    'CIS Controls'
]

def buildBlank():
    return {
        'CIS #': '',
        'Level': '',
        'Title': '',
        'Description': '',
        'Rationale': '',
        'Impact': '',
        'Audit': '',
        'Remediation': '',
        'Default Value': '',
        'References': '',
        'CIS Controls': ''
    }

def parseText(inFileName):
    try:
        with pdfplumber.open(inFileName) as pdf:
            print(f'Parsing {inFileName}')
            outFileName = f'{inFileName}.csv'
            with open(outFileName, 'wt', newline='', encoding='utf-8') as outFile:
                cw = csv.DictWriter(outFile, fieldnames=list(buildBlank().keys()), quoting=csv.QUOTE_ALL)
                cw.writeheader()

                start_processing = False
                row = buildBlank()
                current_field = None
                line_count = 0
                recommendations_found = 0
                potential_recommendation = ''

                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"Processing page {page_num}")
                    lines = page.extract_text().split('\n')
                    for line in lines:
                        line_count += 1
                        line = line.strip()

                        print(f"Line {line_count}: {line[:100]}")

                        if "Recommendations" in line:
                            start_processing = True
                            print("Found 'Recommendations' section. Starting to process...")
                            continue

                        if not start_processing:
                            continue

                        if line.startswith("Appendix: Summary Table"):
                            print("Reached summary table. Stopping processing.")
                            break

                        match = recommendation_pattern.match(line)
                        if match:
                            if row['CIS #']:
                                cw.writerow(row)
                                print(f"Wrote row: CIS # {row['CIS #']}")
                            row = buildBlank()
                            row['CIS #'] = match.group(1)
                            row['Level'] = match.group(2)
                            row['Title'] = match.group(3)
                            current_field = None
                            recommendations_found += 1
                            print(f"New recommendation: {row['CIS #']} - {row['Title']}")
                            continue

                        if any(field in line for field in fields):
                            current_field = next(field for field in fields if field in line)
                            print(f"New field: {current_field}")
                            continue

                        if current_field:
                            row[current_field] += ' ' + line if row[current_field] else line

                    if line.startswith("Appendix: Summary Table"):
                        break

                if row['CIS #']:
                    cw.writerow(row)
                    print(f"Wrote final row: CIS # {row['CIS #']}")

            print(f'Finished processing {inFileName}')
            print(f'Total lines processed: {line_count}')
            print(f'Total recommendations found: {recommendations_found}')

    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Error details: {sys.exc_info()}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputFile', type=str, help='CIS benchmark PDF to parse.')
    args = parser.parse_args()
    parseText(args.inputFile)
