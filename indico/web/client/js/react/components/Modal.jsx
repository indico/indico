/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import React from 'react';
import ReactModal from 'react-modal';
import PropTypes from 'prop-types';

import Slot from 'indico/react/util/Slot';

import './style/modal.scss';


export default class Modal extends React.Component {
    static propTypes = {
        title: PropTypes.string.isRequired,
        children: PropTypes.node.isRequired,
        onClose: PropTypes.func,
        contentLabel: PropTypes.string,
    };

    static defaultProps = {
        onClose: () => {},
        contentLabel: 'Indico Modal Dialog'
    };

    constructor(props) {
        super(props);
        this.open = this.open.bind(this);
        this.close = this.close.bind(this);
        this.state = {
            isOpen: false
        };
    }

    open() {
        this.setState({
            isOpen: true
        });
    }

    close() {
        const {onClose} = this.props;
        this.setState({
            isOpen: false
        });
        onClose.call(this);
    }

    render() {
        const {title, children, contentLabel} = this.props;
        const {isOpen} = this.state;
        const {content, footer} = Slot.split(children);

        return (
            <ReactModal appElement={document.body}
                        className="modal-dialog"
                        overlayClassName="modal-overlay"
                        bodyOpenClassName="modal-overlay-open"
                        isOpen={isOpen}
                        shouldCloseOnEsc
                        shouldCloseOnOverlayClick
                        onRequestClose={this.close}
                        contentLabel={contentLabel}>
                <div className="modal-dialog-header flexrow f-j-space-between">
                    <h2 className="modal-dialog-title">{title}</h2>
                    <a className="i-button text-color borderless icon-cross"
                       onClick={this.close} />
                </div>
                <div className="modal-dialog-content">
                    {content}
                </div>
                {footer && (
                    <div className="modal-dialog-footer">
                        {footer}
                    </div>
                )}
            </ReactModal>
        );
    }
}
