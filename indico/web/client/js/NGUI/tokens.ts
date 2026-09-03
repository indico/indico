// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/** Core palette: Button, Tag, Icon, Timeline Dot */
export type IndicoPaletteColor = 'primary' | 'gray' | 'success' | 'warning' | 'error';

/** Core palette plus 'white', for components that support a light-on-dark look */
export type ExtendedIndicoPaletteColor = IndicoPaletteColor | 'white';

/**
 * Legacy Semantic UI palette — kept for compatibility with data that still
 * comes from the old color scheme (e.g. event labels set by instance
 * managers). Semantic UI spells it "grey", not "gray"
 */
export type LegacyColor =
  | 'red'
  | 'orange'
  | 'yellow'
  | 'olive'
  | 'green'
  | 'teal'
  | 'blue'
  | 'violet'
  | 'purple'
  | 'pink'
  | 'brown'
  | 'grey'
  | 'black';

export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type Variant = 'solid' | 'light' | 'white' | 'transparent';
export type TextWeight = 'regular' | 'bold';
export type IconPosition = 'left' | 'right';

export const DEFAULT_COLOR: IndicoPaletteColor = 'primary';
export const DEFAULT_SIZE: Size = 'md';
export const DEFAULT_VARIANT: Variant = 'solid';
export const DEFAULT_TEXT_WEIGHT: TextWeight = 'regular';
