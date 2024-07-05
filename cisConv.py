#!/usr/bin/env python3

import argparse
import csv
import re
import pdfplumber
import sys

# Updated regular expression to match recommendation lines
recommendation_pattern = re.compile(r'(\d+\.\d+)\s+\((L\d+)\)\s+(.+?)\s+(?:\(Manual\)|\(Automated\))')

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

def extract_field_content(text, field, next_fields):
    pattern = rf'{re.escape(field)}:(.*?)(?={"|".join(map(re.escape, next_fields))}|CIS Controls:|$)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        content = re.sub(r'Page \d+', '', content)
        content = re.sub(r'\n+', '\n', content)  # Replace multiple newlines with a single newline
        return content.strip()
    return ''

def parseText(inFileName):
    try:
        with pdfplumber.open(inFileName) as pdf:
            print(f'Parsing {inFileName}')
            outFileName = f'{inFileName}.csv'
            with open(outFileName, 'wt', newline='', encoding='utf-8') as outFile:
                cw = csv.DictWriter(outFile, fieldnames=list(buildBlank().keys()), quoting=csv.QUOTE_ALL)
                cw.writeheader()

                start_processing = False
                full_text = ''
                recommendations_found = 0

                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    print(f"Processing page {page_num}")
                    print(f"First 100 characters: {page_text[:100]}")
                    
                    if "Recommendations" in page_text:
                        start_processing = True
                        print(f"Found 'Recommendations' on page {page_num}")
                    
                    if start_processing:
                        full_text += page_text + '\n'
                    
                    if "Appendix: Summary Table" in page_text:
                        print(f"Found 'Appendix: Summary Table' on page {page_num}")
                        break

                print(f"Total text length: {len(full_text)}")
                print(f"First 500 characters of processed text: {full_text[:500]}")

                recommendations = recommendation_pattern.findall(full_text)
                print(f"Found {len(recommendations)} potential recommendations")

                for i, rec in enumerate(recommendations):
                    cis_num, level, title = rec
                    row = buildBlank()
                    row['CIS #'] = cis_num
                    row['Level'] = level
                    row['Title'] = title

                    start_index = full_text.index(f"{cis_num} ({level})")
                    end_index = full_text.index(f"{recommendations[i+1][0]} ({recommendations[i+1][1]})") if i < len(recommendations) - 1 else len(full_text)
                    section_text = full_text[start_index:end_index]

                    for j, field in enumerate(fields):
                        next_fields = fields[j+1:] + ['Profile Applicability', 'CIS Controls']
                        row[field] = extract_field_content(section_text, field, next_fields)

                    cw.writerow(row)
                    recommendations_found += 1
                    print(f"Processed recommendation: {row['CIS #']} - {row['Title']}")

            print(f'Finished processing {inFileName}')
            print(f'Total recommendations found: {recommendations_found}')

    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Error details: {sys.exc_info()}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputFile', type=str, help='CIS benchmark PDF to parse.')
    args = parser.parse_args()
    parseText(args.inputFile)
