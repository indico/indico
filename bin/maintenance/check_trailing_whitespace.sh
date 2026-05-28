#!/bin/bash
# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

if ! output=$(rg --json -g '!*.{svg,md,po}' -g '!**/tests/**/*.txt' -g '!**/icomoon/selection.json' '[ \t]+$' .); then
    exit 0
fi

output=$(jq -r -s '(.[] | select(.type == "match").data | "file=\(.path.text[2:]),line=\(.line_number),col=\(.submatches[0].start+1),endColumn=\(.submatches[0].end+1)")' <<<"$output")

while IFS= read -r line; do
    echo "::error $line::File contains trailing whitespace"
done <<< $output
exit 1
