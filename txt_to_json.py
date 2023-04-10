from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json

FILE_DELIMITER = '____________________________________________________________'

@dataclass
class Record:
    title: str
    publication_date: str
    last_updated_date: Optional[str]
    subject: List[str]
    links: List[str]
    text: str
    credit: List[str]

"""States for parsing a ProQuest txt export"""
State = Enum('State', [
    # Initial state. We are looking for the first non-empty line which is the title
    'START',
    # The first non-empty line is implicitly the title so we should disambiguate
    'IDLE',  
    'FINDING_TEXT',
])

LINKS = 'Links:'
FULL_TEXT = 'Full text:'
PUBLICATION_DATE = 'Publication date:'
LAST_UPDATED_DATE = 'Last updated:'
SUBJECT = 'Subject:'
CREDIT = 'CREDIT:'

def parse_record(raw: List[str]) -> Record:
    """Parse a record from ProQuest export into a Record object"""
    state = State.START
    title, publication_date, subject, links, text = '', '', [], [], []
    last_updated = None
    for line in raw:
        if state == State.START and line != '':
            title = line.strip()
            state = State.IDLE
        elif state == State.IDLE and line.startswith(LINKS):
            links.append(line.split(LINKS)[1].strip())
            state = State.IDLE
        elif state == State.IDLE and line.startswith(PUBLICATION_DATE):
            date_str = line.split(PUBLICATION_DATE)[1].strip()
            publication_date = datetime.strptime(date_str, '%b %d, %Y').isoformat().split('T')[0]
            state = State.IDLE
        elif state == State.IDLE and line.startswith(LAST_UPDATED_DATE):
            last_updated = datetime.strptime(date_str, '%b %d, %Y').isoformat().split('T')[0]
            state = State.IDLE
        elif state == State.IDLE and line.startswith(SUBJECT):
            subject.extend([v.strip() for v in line.split(SUBJECT)[1].split(';')])
            state = State.IDLE
        elif state == State.IDLE and line.startswith(FULL_TEXT):
            text.append(line.split(FULL_TEXT)[1])
            state = State.FINDING_TEXT
        elif state == State.FINDING_TEXT and line != '':
            text.append(line)
        elif state == State.FINDING_TEXT and line == '':
            state = State.IDLE

    # Turn text into a single string
    text = ' '.join(text)
    # Remove soft hyphens
    text = text.replace('\xad', '')

    # Find the credit in the text
    maybe_credit = text.split(CREDIT)
    credit = []
    if len(maybe_credit) > 1:
        credit = [v.strip() for v in maybe_credit[1].split(';')]
    return Record(title, publication_date, last_updated, subject, links, text, credit)

IN_FILE = 'proquest_export.txt'
OUT_FILE = 'exports.json'

if __name__ == '__main__':
    # Import txt from ProQuest export
    with open(IN_FILE, 'r') as f:
        data = f.read()

        # Split export into individual records
        raw_records = data.split(FILE_DELIMITER)[1:-1]
        print(f'Found {len(raw_records)} records')
        records = [parse_record(record.split('\n')) for record in raw_records]

        uniq_records = {}
        for record in records:
            key = record.title + record.publication_date
            if key not in uniq_records:
                uniq_records[key] = record
            else:
                if uniq_records[key].text != record.text:
                    print(f'Found duplicate: {record.title} {record.publication_date}')
                    print('  Text differs')

        # Write to JSON
        with open(OUT_FILE, 'w') as f:
            f.write(json.dumps([asdict(record) for record in list(uniq_records.values())], indent=4))
