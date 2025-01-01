// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import ReactModal from 'react-modal';

import {Slot, toClasses} from 'indico/react/util';

import './style/modal.scss';

export default class Modal extends React.Component {
  static propTypes = {
    title: PropTypes.string,
    children: PropTypes.node.isRequired,
    onClose: PropTypes.func,
    contentLabel: PropTypes.string,
    header: PropTypes.bool,
    fixedFooter: PropTypes.bool,
  };

  static defaultProps = {
    title: '',
    onClose: () => {},
    contentLabel: 'Indico Modal Dialog',
    header: true,
    fixedFooter: false,
  };

  constructor(props) {
    super(props);
    this.open = this.open.bind(this);
    this.close = this.close.bind(this);
    this.state = {
      isOpen: false,
    };
  }

  open() {
    this.setState({
      isOpen: true,
    });
  }

  close() {
    const {onClose} = this.props;
    this.setState({
      isOpen: false,
    });
    onClose.call(this);
  }

  render() {
    const {header, title, children, contentLabel, fixedFooter} = this.props;
    const {isOpen} = this.state;
    const {content, footer} = Slot.split(children);

    const classes = {
      'modal-dialog': true,
      'modal-with-footer': !!footer && !fixedFooter,
      'modal-with-fixed-footer': fixedFooter,
      'modal-with-header': header,
    };

    return (
      <ReactModal
        appElement={document.body}
        className={toClasses(classes)}
        overlayClassName="modal-overlay"
        bodyOpenClassName="modal-overlay-open"
        isOpen={isOpen}
        shouldCloseOnEsc
        shouldCloseOnOverlayClick
        onRequestClose={this.close}
        contentLabel={contentLabel}
      >
        {header && (
          <div className="modal-dialog-header flexrow f-j-space-between">
            {title && <h2 className="modal-dialog-title">{title}</h2>}
            <a className="i-button text-color borderless icon-cross" onClick={this.close} />
          </div>
        )}
        <div className="modal-overflow-container">
          <div className="modal-dialog-content">{content}</div>
          {footer && <div className="modal-dialog-footer">{footer}</div>}
        </div>
      </ReactModal>
    );
  }
}
