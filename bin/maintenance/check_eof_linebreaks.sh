#!/bin/bash
# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

if ! output=$(rg -Ul -g '!*.svg' -g '!**/icomoon/selection.json' '[^\n]\z' .); then
    exit 0
fi

while IFS= read -r f; do
    lastline=$(( $(wc -l "$f" | cut -d' ' -f1) + 1))
    echo "::error file=${f#./},line=${lastline}::Linebreak missing at end of file"
done <<< $output
exit 1
