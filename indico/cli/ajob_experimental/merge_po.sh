#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <translations_folder>"
    exit 1
fi

translations_dir="$1"
merged_dir="${translations_dir%/}/../merged_translations"

mkdir -p "$merged_dir"

for lang_dir in "$translations_dir"/*/; do
    lang_folder_name=$(basename "$lang_dir")
    
    src_lc_messages="$lang_dir/LC_MESSAGES"
    dest_lc_messages="$merged_dir/$lang_folder_name/LC_MESSAGES"
    
    if [ -d "$src_lc_messages" ]; then
        mkdir -p "$dest_lc_messages"

        msgcat "$src_lc_messages"/*.po -o "$dest_lc_messages/messages_merged.po"
        
        echo "Merged .po files in $src_lc_messages into $dest_lc_messages/messages_merged.po"
    else
        echo "Warning: No LC_MESSAGES folder in $lang_dir. Skipping."
    fi
done

echo "Merging completed. Merged .po files are located in $merged_dir."
