This element is used to add tooltips to elements.

Tooltips are used on interactive clickable elements such as buttons and links.
They are used to supply additional information that may not be quite obvious
from the element itself.

Before resorting to tooltips every effort should be invested into clarifying
the purpose of the element. Tooltips are only available to mouse and keyboard
users. They are still unavailable to users of touch-only devices (e.g.,
smartphones and tablets) because such devices have no ability to hover or
focus specific elements. Please also note that tooltips should never be used
on non-focusable elements.

To add a tooltip, wrap the target element and the tooltip content in the
`<ind-with-tooltip>` custom element. The tooltip content is marked using the
`data-tip-content` attribute. The tip content should be part of the element's
label.

Example:

```html
<ind-with-tooltip>
    <button>
        <span data-tip-content>Load data from a file</span>
    </button>
</ind-with-tooltip>
```

In the example above, the button is styled such that it only shows an icon
using the `::before` or `::after` pseudo-element. The tip content is
hidden by default and is revealed as a tooltip when the button is hovered
or focused.

In some cases, the target element may contain on-tip text that is partly
duplicated in the tip. For instnace, a button may have a text label
'Load' and the tip may repeat this word: 'Load from file'. In such cases
we suppress the visible text label using `aria-hidden="true"`. This
keeps the text visible but doesn't read it to the users of accessibility
technology.

Example:

```html
<ind-with-tooltip>
    <button>
        <span aria-hidden="true">Load</span>
        <span data-tip-content>Load from file</span>
    </button>
</ind-with-tooltip>
```

The above example only applies to cases where there is overlap between the
tip text and non-tip text. In cases where the tip and non-tip text don't
overlap, we can simply leave them as is.

Example:

```
<ind-with-tooltip>
    <button>
        Import
        <span data-tip-content>Load data from a file</span>
    </button>
</ind-with-tooltip>
```
