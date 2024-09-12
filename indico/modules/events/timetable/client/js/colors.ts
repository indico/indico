export const ENTRY_COLORS = [
  // childColor is baed on the backgroundColor of the parent
  // If the parent textColor is dark, the childColor is lighter than the parent backgroundColor
  // If the parent textColor is light, the childColor is darker than the parent backgroundColor
  {textColor: '#1d041f', backgroundColor: '#eee0ef', childColor: '#c0a0c0'},
  {textColor: '#253f08', backgroundColor: '#e3f2d3', childColor: '#a0c080'},
  {textColor: '#1f1f02', backgroundColor: '#feffbf', childColor: '#c0c0a0'},
  {textColor: '#202020', backgroundColor: '#dfe555', childColor: '#a0a020'},
  {textColor: '#1f1d04', backgroundColor: '#ffec1f', childColor: '#c0b010'},
  {textColor: '#0f264f', backgroundColor: '#dfebff', childColor: '#a0b0c0'},
  {textColor: '#eff5ff', backgroundColor: '#0d316f', childColor: '#5070a0'},
  {textColor: '#f1ffef', backgroundColor: '#1a3f14', childColor: '#609060'},
  {textColor: '#ffffff', backgroundColor: '#5f171a', childColor: '#a06060'},
  {textColor: '#272f09', backgroundColor: '#d9dfc3', childColor: '#a0a080'},
  {textColor: '#ffefff', backgroundColor: '#4f144e', childColor: '#a060a0'},
  {textColor: '#ffeddf', backgroundColor: '#6f390d', childColor: '#a07050'},
  {textColor: '#021f03', backgroundColor: '#8ec473', childColor: '#608040'},
  {textColor: '#03070f', backgroundColor: '#92b6db', childColor: '#506080'},
  {textColor: '#151515', backgroundColor: '#dfdfdf', childColor: '#a0a0a0'},
  {textColor: '#1f1100', backgroundColor: '#ecc495', childColor: '#c0a060'},
  {textColor: '#0f0202', backgroundColor: '#b9cbca', childColor: '#80a0a0'},
  {textColor: '#0d1e1f', backgroundColor: '#c2ecef', childColor: '#80a0a0'},
  {textColor: '#000000', backgroundColor: '#d0c296', childColor: '#a0a080'},
  {textColor: '#202020', backgroundColor: '#efebc2', childColor: '#c0c0a0'},
];

export const ENTRY_COLORS_BY_BACKGROUND = Object.fromEntries(
  ENTRY_COLORS.map(({backgroundColor, ...colors}) => [backgroundColor, colors])
);
