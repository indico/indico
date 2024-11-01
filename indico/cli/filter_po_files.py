import os
import re

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po


def should_include(message):
    pattern = r'''(
        \{[^}]*\}    # Match closing curly brace (incl. empty)
        |            # OR
        \%\([^)]+\)  # Match closing parenthesis
        [sdf]        # Match format type (string, decimal, float)
    )
    '''

    if isinstance(message.id, tuple):
        return all(len(re.findall(pattern, id, re.VERBOSE)) <= 0 for id in message.id)

    return len(re.findall(pattern, message.id, re.VERBOSE)) <= 0


def filter_po_files(merged_dir):
    for lang_dir in os.listdir(merged_dir):
        lang_path = os.path.join(merged_dir, lang_dir, 'LC_MESSAGES', 'messages_merged.po')
        
        if os.path.isfile(lang_path):            
            with open(lang_path, 'rb') as po_file:
                catalog = read_po(po_file)     
                filtered_catalog = Catalog()

                for message in catalog:                    
                    if should_include(message):
                        filtered_catalog[message.id] = message
            
            with open(lang_path, 'wb') as po_file:
                write_po(po_file, filtered_catalog)
            
            print(f'Filtered messages in {lang_path}')


def main():
    merged_dir = input('Enter path to merged translations folder: ').strip()
    filter_po_files(merged_dir)
    print('Filtering done')


if __name__ == '__main__':
    main()
