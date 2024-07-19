// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export default class CustomElementBase extends HTMLElement {
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

  disconnectedCallbasck() {
    this.dispatchEvent(new Event('x-disconnect'));
  }
}
