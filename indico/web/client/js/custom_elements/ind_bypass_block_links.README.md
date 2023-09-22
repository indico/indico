This element is used to create a set of bypass block [links][1] in the page. The
custom element is added to the base template, so there is no need to add it
manually anywhere on the page.

The bypass block links are created by marking elements on the page as a bypass
block target. The target element is usually a heading. For an element to be a
valid target, it must have the 'id' and 'data-bypass-target' attributes. The
'data-bypass-target' should contain a text that will be used as the label for
the bypass block link.

Example:

```html
<h2 id="category-list" data-bypass-target="{% trans %}Skip to category list{% endtrans %}">
    {% trans %}Category list{% endtrans %}
</h2>
```

Note that the bypass block link target does not need to be visible on the
page. The utility placeholder selector can be used to hide it. For example:

```scss
@use "base/utilities";

#category-list {
    @extend %visually-hidden;
}
```

[1]: https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html
