# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
import sys
from pathlib import Path


# Emojis for headings. This also serves as an exhaustive list of allowed headings
EMOJIS = {
    'Blog Post': ':bulb:',
    'Major Features': ':trophy:',
    'Major Changes': ':trophy:',
    'Security fixes': ':warning:',
    'Internationalization': ':flags:',
    'Improvements': ':tada:',
    'Bugfixes': ':bug:',
    'Accessibility': ':wheelchair:',
    'Internal Changes': ':wrench:',
}


def fail(msg):
    """Fail with a nice error message in GitHub actions."""
    print(f'::error::{msg}')
    sys.exit(1)


def extract_changelog(text, version, *, allow_unreleased=False):
    """Extract the changelog for a given version."""
    start_re = rf'^Version {re.escape(version)}\n-+\n\n\*(Unreleased|Released on .+)\*\n$'
    end_re = r'(^----$)|(^Version [0-9.abrc]+$)'

    if not (match := re.search(start_re, text, re.MULTILINE)):
        fail(f'Version {version} not found in text')
    if match.group(1) == 'Unreleased' and not allow_unreleased:
        fail(f'Version {version} is marked as unreleased')

    text = text[match.end():]

    # try to find the next version or separator between big releases. if we don't find one
    # we assume we're at the end of the file and just take everything.
    if match := re.search(end_re, text, re.MULTILINE):
        text = text[:match.start()]

    return text.strip()


def _replace_unsplit(prefix):
    def _replacer(match):
        refs = [x.strip() for x in match.group(1).split(',')]
        return ', '.join(f'{prefix}{ref}' for ref in refs)
    return _replacer


def convert_to_markdown(text):
    """Convert rst changelog to markdown.

    This is a poor man's rst-to-markdown converter that just handles the stuff
    we use in our CHANGES.rst file. Using it avoids having to install a tool
    like pandoc and it also does some nice extra things such as adding emojis
    to headings (or failing if an unknonwn heading is used).
    """
    # github references
    text = re.sub(r':(?:issue|pr):`([\d, ]+)`', _replace_unsplit('#'), text)  # issue/pr
    text = re.sub(r':user:`([^`]+)`', _replace_unsplit('@'), text)  # user
    text = re.sub(r':cve:`([^`]+)`', _replace_unsplit(''), text)  # CVE
    # documentation references
    text = re.sub(r':data:`([^`]+)`', r'[`\1`](https://docs.getindico.io/en/stable/config/settings/#\1)', text)
    text = re.sub(r':ref:`([^<]+) <[^>]+>`', r'\1', text)
    # headings
    text = re.sub(r'^([A-Z a-z]+)\n\^+$', lambda m: f'# {EMOJIS[m.group(1)]} {m.group(1)}', text, flags=re.MULTILINE)
    # external links
    text = re.sub(r'`([^`<]+) <([^>]+)>`_{1,2}', r'[\1](\2)', text)
    # inline code/monospace
    text = text.replace('``', '`')
    # wrapped bullet points & note blocks
    new_lines = []
    in_bullet_point = in_note = False
    note_lines = []
    for line in text.splitlines():
        # bullet points
        if line.startswith('- '):
            in_bullet_point = True
            new_lines.append(line)
            continue
        if in_bullet_point and line.startswith('  '):
            # anything indented with two spaces right after a bulleted line is consindered
            # a continuation of that bullet point
            new_lines[-1] += line[1:]
            continue
        in_bullet_point = False
        # notes
        if line == '.. note::':
            in_note = True
            continue
        if in_note:
            if not note_lines and not line.strip():
                # swallow empty lines between the note marker and the first content line
                continue
            if line.startswith('    '):
                # any indented line in a note block is part of the note
                note_lines.append(line.strip())
                continue
            new_lines.append('Note: ' + ' '.join(note_lines))
            in_note = False
            note_lines.clear()
            # fall through to the default below, this is typically the blank line right
            # after the note which we want to keep
        # anything that doesn't need special handling
        new_lines.append(line)
    return '\n'.join(new_lines)


def main():
    version = sys.argv[1]
    try:
        destfile = Path(sys.argv[2])
    except IndexError:
        destfile = None
    changelog = Path('CHANGES.rst').read_text()
    changelog = extract_changelog(changelog, version, allow_unreleased=(not destfile))
    changelog = convert_to_markdown(changelog)
    if not destfile:
        print(changelog)
        return
    destfile.write_text(changelog)


if __name__ == '__main__':
    main()
