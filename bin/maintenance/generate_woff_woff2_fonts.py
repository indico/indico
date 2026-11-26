#!/usr/bin/env python
# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import click
from fontTools.ttLib import TTFont


SOURCE_FONT_TYPES = ('ttf', 'otf')
TARGET_FONT_TYPES = ('woff', 'woff2')


def generate_target_font_types(source_path, overwrite):
    all_generated = True
    for target_type in TARGET_FONT_TYPES:
        if not overwrite and source_path.with_suffix(f'.{target_type}').is_file():
            click.secho(
                f'Skipped {source_path} -> .{target_type} File already exists and no repeat mode is selected',
                fg='yellow',
            )
            all_generated = False
            continue
        out_path = source_path.with_suffix(f'.{target_type}')
        with TTFont(source_path, recalcBBoxes=True) as file:
            file.flavor = target_type
            file.save(out_path)
        click.secho(f'Converted: {source_path.name} -> {out_path.name}', fg='green')
    return all_generated


@click.command(help='Generate .woff and .woff2 files for every .ttf and .otf font file in '
    'indico/web/static/fonts and its subdirectories.')
@click.option(
    '--delete-source',
    default=False,
    is_flag=True,
    help='Delete the original .ttf/.otf files after its .woff and .woff2 were generated. '
    'Sources whose conversion was skipped (see --overwrite) or failed are kept. False by default. ',
)
@click.option(
    '--overwrite',
    default=False,
    is_flag=True,
    help='Regenerate .woff and .woff2 files even if they already exist. False by default. ',
)
def main(delete_source, overwrite):
    indico_root = Path(__file__).parents[2]
    web_dir = indico_root / 'indico' / 'web'
    fonts_dir = web_dir / 'static' / 'fonts'

    for source_font_type in SOURCE_FONT_TYPES:
        for source_font_file in fonts_dir.rglob(f'*.{source_font_type}', case_sensitive=False):
            try:
                generated = generate_target_font_types(source_font_file, overwrite)
            except Exception as err:
                click.secho(f'Failed to generate {source_font_type} for {source_font_file}: {err}', fg='red')
                continue
            if delete_source and generated:
                try:
                    source_font_file.unlink()
                    click.secho(f'Removed {source_font_file}', fg='green')
                except Exception as err:
                    click.secho(f'Failed to remove {source_font_file}: {err}', fg='red')


if __name__ == '__main__':
    main()
