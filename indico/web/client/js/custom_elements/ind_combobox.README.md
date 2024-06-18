This element controls combo box form controls with inline autocompletion.

Inline combo box controls are inputs that will show available options that match
the user input as the user types.

The combo box operates in two modes depending on whether the `aria-autocomplete`
attribute is set on the input. When `aria-autocomplete` is set to `both`, then
the first available option (if any) will be automatically inserted into the
input, and the text following what was already typed will be selected so that
the typing can continue unhindered on the next keystroke. Otherwise, the list is
simplly filtered based on the keyword.

NOTE: This document describes the usage of the `<ind-combo-box>` custom element.
In React, the `ComboBox` component should be used instead, which provides a
higher level interface. This components handles some of the idiosyncrasies of
integrating native components into React applications.

Please note that a combo box is not the same as a select list. Because a combo
box is a glorified text field, the values used in the combo box must be
human-readable. This is different from the select lists where the value and the
label associated with the value are not necessarily the same. This means that,
if you are mapping human-readable labels to some internal values, you will need
to do some translation. You can see an example of a React component that
translates between human-readable and internal values in the `SingleChoiceInput`
component.

All event handling is done on the `<input>` element. When the user is typing,
the 'input' event is triggered as usual. When the selection is made using arrow
keys or clicking on options directly, the 'change' event is dispatched, to mimic
the behavior of select lists.

The options are specified using a list. Typically this is a `<ul>` element with
`<li>` children, but alternative markups are supported as long as the following
conditions are met:

- The element containing the list must have `role="listbox"`
- The options must be direct children of the container
- The options must have `role="option"`

The `data-value` attribute of the option elements will be used to autocomplete
the input. If the option has no `data-value` attribute, it will be treated as
a blank string. Although multiple such options are allowed, it does not make
sense to have more than one.

Example:

```html
<label>
    <span>Title:</span>
    <ind-combo-box value="Mr.">
        <input type="text" role="combobox" required>
        <ul role="listbox">
            <li role="option">Unspecified</li>
            <li role="option" data-value="Mr.">Mr.</li>
            <li role="option" data-value="Mrs.">Mrs.</li>
            <li role="option" data-value="Ms.">Ms.</li>
            <li role="option" data-value="Mx">Mx</li>
            <li role="option" data-value="Dr">Dr</li>
        </ul>
    </ind-combo-box>
</label>
```

The option label can contain any markup. However, it is generally best to avoid
presenting overly complex information in options, as the user may attempt to
quickly scan the options using a screen reader, and having too much information
can be time-consuming.

Disabled options are marked using `aria-disabled="true"` attribute on the
`[role="option"]` elements. Disabled options cannot be selected and will not be
shown in the autocomplete list.

An optional button to clear the input can be added to the widget. To do this,
add a `<button value="clear">` element with appropriate label into the
`<ind-combo-box>` element. Usually it is placed at the end, after the listbox.
There is no need to instrument this button as that is taken care of by
`<ind-combo-box>` itself. This button is only shown if the input is not
`required`.
