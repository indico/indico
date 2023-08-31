# Indico Design System

The SCSS design system for Indico.

This design system is intended for use exclusively with the `@extend`
feature. It does not provide any mixins, SCSS variables, and similar.

## Basic usage

The intended usage is as follows:

```scss
@use 'design_system';

some-selector {
  @extend %generic-container;
  --container-element-spacing: 1em;
}
```

This results in the following output:

```css
some-selector {
  %generic-container declarations....
}

some-selector {
  --container-element-spacing: 1em;
}
```

Customization is done using CSS variables. They can be defined either
on the selected element itself, or one of its ancestors. Using CSS
variables on ancestors allows us to target any of its descendants, so
we are able to override the styles for a particular region of the page.

```scss
some-region {
  --control-clickable-surface-color: #{$some-other-color};
}

some-selector {
  @extend %generic-container;
  --container-element-spacing: 1em;
}
```

## Background

This is decidedly different from the common way of using CSS in which the
appearance of the element is defined using classes. Instead of adding
classes to elements in order to specify their appearance, we instead use
placeholder selectors and `@extend` to specify the appearance for elements
selected by the selector. However, in a way, it is also similar to how the
class-based CSS works, in that we use the placeholder selectors the same
way we use classes.

This approach has the following benefits:

- It reduces the amount of markup being sent over the wire (all elements
  need a single class at most).
- It restricts all appearance-related changes to the stylesheet.


## Why extends and not mixins

The placeholder selectors are not mixins. They do not take parameters.
Instead, we use CSS variables to customize the appearance of the
elements. This is a deliberate trade-off to avoid duplicating CSS
across different selectors (with `@extend`, the selector is moved to the
placeholder's declaration block, rather than the other way around).

CSS variables also allow the third party stylesheet to override various
aspects of the visual appearance using plain CSS. Another advantage of CSS
variables is that they are subject to CSS cascade, so they can be used by
the parent to override appearance for its descendants, etc.


## Media queries

One trade-off of using the `@extend` method is that placeholder selectors
cannot be used in media queries. The following code shows why:

```scss
%placeholder {
  flex: none;
  width: 2em;
}

@media (width < 45em) {
  .foo {
    @extend %placeholder;
  }
}
```

The above code would have to compile to this:

```scss
.foo {
  flex: none;
}

@media (width < 45em) {
  .foo { }
}
```

If SCSS were to compile the code the way we instructed, it would break the
media query. Within at-rules, we still need to use mixins. In most cases, this
can be achieved by converting the placeholder selector into a mixin like so:

```scss
@mixin placeholder {
  flex: none;
  width: 2em;
}

%placeholder {
  @include placeholder();
}

// ...

@media (width < 45em) {
  .foo {
    @include placeholder;
  }
}
```

Please be careful when converting placeholder selector that extend other
placeholder selectors. Such placeholders cannot be converted into a mixin
and you will need to figure out a different approach. However, in most
cases such complex placeholder selectors are not intended for use within
media queries to begin with, so do first check that what you're trying to
do actually makes sense.

## Maintenance

In order to keep this system working, please keep in mind the following
rules of thumb:

- All variable parameters that are shared among the modules in this folder
  should be defined *as CSS variables* in the `variables.scss` module.
- All SCSS modules in this folder should only use CSS variables except for
  the `variables.scss` module, which can use SCSS variables as well.
- The CSS variable name loosely follows the following convention:

```scss
--{TOPIC}-{ELEMENT/SUBTOPIC}-{CHARACTERISTIC}
```

- Ensure the CSS variable names are searchable as there are no mechanisms
  to spot typos.
- Placeholder selectors contain information about the structure of the
  elements they apply to. Do not require the developer to add classes to
  the target elements if not needed. Do not over-prescribe the layout of
  the elements if not needed: keep it as flexible as possible (this means
  you need to keep the nesting to the minimum, among other things, one
  level for namespacing, and sometimes another one for pseudo-classes or
  pseudo-elements is enough).
