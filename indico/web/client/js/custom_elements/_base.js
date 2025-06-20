// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {toOptionalDate} from 'indico/utils/date';
import {domReady} from 'indico/utils/domstate';

const isPrototypeOf = Object.prototype.isPrototypeOf;

function toKebabCase(propertyName) {
  return propertyName.replace(/[^A-Z][A-Z]/g, s => `${s[0]}-${s[1].toLowerCase()}`).toLowerCase();
}

export default class CustomElementBase extends HTMLElement {
  static CustomAttribute = class {
    static isSubclass(Other) {
      return isPrototypeOf.call(this.prototype, Other.prototype);
    }

    constructor(element, attrName) {
      this.element = element;
      this.name = attrName;
    }

    getValue() {
      return this.element.getAttribute(this.name);
    }

    setValue(value) {
      this.element.setAttribute(this.name, value);
    }
  };

  static setValue = (element, value) => {
    // This is a hack to bypass the setter that React adds to the
    // value property. Apparently, modifying a value before firing
    // an event will cause React to not handle the event at all,
    // probably because it expects values to only ever be modified
    // through React.
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(element, value);
  };

  static define(tagName, subclass) {
    console.assert(
      Object.prototype.isPrototypeOf.call(CustomElementBase.prototype, subclass.prototype),
      'Must extends CustomElementBase'
    );
    customElements.define(tagName, subclass);
  }

  static defineWhenDomReady(tagName, subclass) {
    domReady.then(() => {
      this.define(tagName, subclass);
    });
  }

  /**
   * Specification of attributes that will be used in the
   * custom element.
   *
   * The attributes object maps from property names in camel-case
   * to the specification objects. Property names are specified
   * in camelCase and that is the name you will be using to access
   * them within JavaScript. The attribute names are derived from
   * these propertyNames by kebab-casing them. For example, if you
   * specify a property 'minValue', you will be accessing it as
   * `this.minValue`, or `this.getAttribute('min-value')`. This keeps
   * things consistent with native elements.
   *
   * The specification objects can be constructor functions `String`
   * or `Boolean`, `Number`, `Date`, or an object with the following
   * properties:
   *
   * - `type` (required) - either `String`, `Boolean`, `Number`, `Date`
   * - `readonly` (optional) - `true` or `false` (default: `false`)
   * - `default` (optional) - any value (default: `null`)
   *
   * The `Boolean` attributes' value is always a Boolean, and the
   * presence of the attribute represents the value (think
   * `disabled` or `checked` attributes in HTML). When setting the
   * value, the truthiness of the value is used to add or remove the
   * attribute.
   *
   * The `Number` attributes' value is a number or a `NaN` if the
   * attribute is not present or is set to a non-numeric value.
   *
   * The `Date` attributes' value is a `Date` object or `null` if
   * set to a value that cannot be parsed as a date. When setting
   * the date, it will be set to an RFC 2822 format (e.g.,
   * 'Thu, 01 Sep 2016') by invoking the `.toDateString()` method on
   * the value. If the value being set is a string, it will be set as
   * is. If the value is not a string, and also not have a
   * `.toDateString()` method (it doesn't have to be a `Date` object),
   * it is replaced with an empty string.
   *
   * The `String` attributes are normal attirbutes, and their value
   * is always string. Any value set on this attribute will be coerced
   * into string.
   *
   * By default, attributes listed in this object are automatically
   * observed. If you wish to observe only some of them, you should
   * manually set the `observedAttributes` static property.
   */
  static attributes = {};

  static get observedAttributes() {
    return Object.keys(this.attributes);
  }

  constructor() {
    super();

    for (const propertyName in this.constructor.attributes) {
      let attributeSpec = this.constructor.attributes[propertyName];
      if (typeof attributeSpec === 'function') {
        attributeSpec = {type: attributeSpec};
      }
      const defaultValue = attributeSpec.default ?? null;
      const attributeName = toKebabCase(propertyName);
      let getter, setter;

      if (this.constructor.CustomAttribute.isSubclass(attributeSpec.type)) {
        const Attr = attributeSpec.type;
        const attr = new Attr(this, attributeName);
        getter = attr.getValue.bind(attr);
        setter = attr.getValue.bind(attr);
      } else {
        switch (attributeSpec.type) {
          case Boolean:
            getter = function() {
              return this.hasAttribute(attributeName);
            };
            setter = function(value) {
              this.toggleAttribute(attributeName, value);
            };
            break;
          case Number:
            getter = function() {
              return Number(this.getAttribute(attributeName));
            };
            setter = function(value) {
              this.setAttribute(attributeName, value ?? '');
            };
            break;
          case Date:
            getter = function() {
              return toOptionalDate(this.getAttribute(attributeName));
            };
            setter = function(value) {
              if (typeof value === 'string') {
                this.setAttribute(attributeName, value);
              } else {
                this.setAttribute(attributeName, value?.toDateString?.() || '');
              }
            };
            break;
          default:
            getter = function() {
              return this.getAttribute(attributeName) ?? defaultValue;
            };
            setter = function(value) {
              this.setAttribute(attributeName, value);
            };
        }
      }
      const descriptor = {
        get: getter,
      };
      if (!attributeSpec.readonly) {
        descriptor.set = setter;
      }
      Object.defineProperty(this, propertyName, descriptor);
    }
  }

  connectedCallback() {
    // Custom elements may get temporarily disconnected. Since the
    // setup method may run operations that should not be repeated
    // (e.g., set up the DOM,  attach event listeners for elements
    // in the subtree), it is disabled after the first run.
    //
    // There are operations that should be repeated on every
    // connect, and undone on every disconnect in order to prevent
    // memory leaks or double-registration. These are operations
    // such as attaching global event listeners. This class will
    // emit the x-connect and x-disconnect events on every connect
    // and disconnect, and the setup() method is expected to set up
    // listeners that will perform such operations.

    this.setup?.();
    this.setup = null;
    this.dispatchEvent(new Event('x-connect'));
  }

  setup() {
    throw Error('Custom element must implement a setup() method');
  }

  disconnectedCallback() {
    this.dispatchEvent(new Event('x-disconnect'));
  }

  attributeChangedCallback(name) {
    const eventName = this.constructor.attributes[name]?.changeEventAlias ?? name;
    this.dispatchEvent(new Event(`x-attrchange.${eventName}`));
    this.dispatchEvent(new Event('x-attrchange'));
  }
}
