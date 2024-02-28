This element is used to add toggletips to a dedicated toggletip button.

Toggletips are buttons with just one purpose: open a popup message similar to a
tooltip. They are usually styles as info buttons (circle with lower-case i or
questionmark). Since tooltips can only supply non-critical messages on
interactive elements, toggletips are used in cases where extra information must
be supplied but no interactive elements are involved.

Toggletips are created by placing the target button and tip content inside a
`<ind-with-toggletip>` element. The tip content is marked using the
`data-tip-content` attribute, and it also marked as a live region by giving
it the `aria-live="polite"` attribute.

By setting the `aria-live` attribute on the element, we cause the screen
readers and similar accessibility technology to read the tooltip when the
button is activated.

Example:

```html
<ind-with-toggletip>
  <button>More information</button>
  <div data-tip-content aria-live="polite">
    The toggle tip content...
  </div>
</ind-with-toggletip>
```

Note: When working with React app, you may sometimes observe that the
toggle tip content does not change. The DOM nodes in the tree may change
but the old text is still displayed. Alternatively, you may get a
`DOMException`. This happens because the custom element manupulates the
contents of the `[data-tip-content]` element. To work around this, ensure
that React cleanly replaces the entire custom element with a new one by
giving the `<ind-with-toggletip>` element a `key` prop. The key should be
such that it changes whenever the tip contents change.
