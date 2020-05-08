// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Translate} from 'indico/react/i18n';

// base colors (must match entries in _palette.scss)
const Palette = {
  blue: '#5d95ea',
  grey: '#bbb',
  yellow: '#e99e18',
  red: '#f91f1f',
  green: '#00c851',
  purple: '#6e5494',
  orange: '#f80',
};

// colors for specific purposes
Palette.highlight = Palette.blue;

export const SUIPalette = {
  red: Translate.string('Red'),
  orange: Translate.string('Orange'),
  yellow: Translate.string('Yellow'),
  olive: Translate.string('Olive'),
  green: Translate.string('Green'),
  teal: Translate.string('Teal'),
  blue: Translate.string('Blue'),
  violet: Translate.string('Violet'),
  purple: Translate.string('Purple'),
  pink: Translate.string('Pink'),
  brown: Translate.string('Brown'),
  grey: Translate.string('Grey'),
  black: Translate.string('Black'),
};
export default Palette;
