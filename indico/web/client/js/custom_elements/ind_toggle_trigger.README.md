This element is used to wrap a control that controls the visibilty of another element.

The element expects to find at least one element with an `aria-controls` attribute, which
is expected to be an id of the controlled element (this is the attribute's standard usage).
It will try to locate the controlled element based on the attribute value. If it does not
find one, it will hide the control.

The controlled element is toggled by toggling the `hidden` attribute. The controlled
element's default state is determined based on the attribute. If you need to perform some
action (or animate) during toggling, you can use a custom element as a target (see
`ind_seesion_menu.js` for an example).

Example:

```
<ind-toggle-trigger>
    <button aria-controls="foo">Open</button>
</ind-toggle-trigger>

<section id="foo" hidden>
    Closed now
</section>
```
