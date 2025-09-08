// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const DEFAULT_CONTRIB_COLORS = {
  color: '#ffffff',
  backgroundColor: '#5b1aff',
};

export const DEFAULT_BREAK_COLORS = {
  color: '#000000de',
  backgroundColor: '#cce2ff',
};

export const ENTRY_COLORS = [
  // childColor is baed on the backgroundColor of the parent
  // If the parent text color (color) is dark, the childBackgroundColor is lighter than the parent backgroundColor
  // If the parent text color (color) is light, the childBackgroundColor is darker than the parent backgroundColor
  {color: '#1d041f', backgroundColor: '#eee0ef', childBackgroundColor: '#c0a0c0'},
  {color: '#253f08', backgroundColor: '#e3f2d3', childBackgroundColor: '#a0c080'},
  {color: '#1f1f02', backgroundColor: '#feffbf', childBackgroundColor: '#c0c0a0'},
  {color: '#202020', backgroundColor: '#dfe555', childBackgroundColor: '#a0a020'},
  {color: '#1f1d04', backgroundColor: '#ffec1f', childBackgroundColor: '#c0b010'},
  {color: '#0f264f', backgroundColor: '#dfebff', childBackgroundColor: '#a0b0c0'},
  {color: '#eff5ff', backgroundColor: '#0d316f', childBackgroundColor: '#5070a0'},
  {color: '#f1ffef', backgroundColor: '#1a3f14', childBackgroundColor: '#609060'},
  {color: '#ffffff', backgroundColor: '#5f171a', childBackgroundColor: '#a06060'},
  {color: '#272f09', backgroundColor: '#d9dfc3', childBackgroundColor: '#a0a080'},
  {color: '#ffefff', backgroundColor: '#4f144e', childBackgroundColor: '#a060a0'},
  {color: '#ffeddf', backgroundColor: '#6f390d', childBackgroundColor: '#a07050'},
  {color: '#021f03', backgroundColor: '#8ec473', childBackgroundColor: '#608040'},
  {color: '#03070f', backgroundColor: '#92b6db', childBackgroundColor: '#506080'},
  {color: '#151515', backgroundColor: '#dfdfdf', childBackgroundColor: '#a0a0a0'},
  {color: '#1f1100', backgroundColor: '#ecc495', childBackgroundColor: '#c0a060'},
  {color: '#0f0202', backgroundColor: '#b9cbca', childBackgroundColor: '#80a0a0'},
  {color: '#0d1e1f', backgroundColor: '#c2ecef', childBackgroundColor: '#80a0a0'},
  {color: '#000000', backgroundColor: '#d0c296', childBackgroundColor: '#a0a080'},
  {color: '#202020', backgroundColor: '#efebc2', childBackgroundColor: '#c0c0a0'},
];

export const ENTRY_COLORS_BY_BACKGROUND = Object.fromEntries(
  ENTRY_COLORS.map(({backgroundColor, color, childBackgroundColor}) => [
    backgroundColor,
    {color, backgroundColor: childBackgroundColor},
  ])
);
