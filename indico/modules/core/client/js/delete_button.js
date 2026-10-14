// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import GenericDeleteButton from './DeletionDialog';

customElements.define(
  'ind-delete-button',
  class extends HTMLElement {
    connectedCallback() {
      requestAnimationFrame(() => {
        ReactDOM.render(
          <GenericDeleteButton
            title={this.getAttribute('dialog-title')}
            buttonLabel={this.getAttribute('button-label')}
            message={this.getAttribute('message')}
            cancelText={this.getAttribute('cancel-text')}
            confirmText={this.getAttribute('confirm-text')}
            recordName={this.getAttribute('record-name')}
            deleteURL={this.getAttribute('delete-url')}
            redirectURL={this.getAttribute('redirect-url')}
            isDisabled={JSON.parse(this.getAttribute('is-disabled') || 'false')}
            disabledMessage={this.getAttribute('disabled-message')}
            icon={this.getAttribute('icon')}
            iconColor={this.getAttribute('icon-color')}
            childrenHTML={this.innerHTML}
            countdownSeconds={this.getAttribute('countdown-seconds') || 10}
            method={this.getAttribute('method')}
            dataParams={this.getAttribute('data-params')}
            buttonClass={this.getAttribute('button-class') || undefined}
          />,
          this
        );
      });
    }
  }
);
