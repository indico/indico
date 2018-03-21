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
import PropTypes from 'prop-types';

import Modal from 'indico/react/components/Modal';
import IButton from 'indico/react/components/IButton';

export default class LogEntryModal extends React.Component {
    static propTypes = {
        entries: PropTypes.array.isRequired,
        currentViewIndex: PropTypes.number,
        setDetailedView: PropTypes.func.isRequired
    };

    static defaultProps = {
        currentViewIndex: null
    };

    constructor(props) {
        super(props);
        this.modal = undefined;
        this.onClose = this.onClose.bind(this);
    }

    componentDidUpdate() {
        const {currentViewIndex} = this.props;
        if (currentViewIndex !== null) {
            this.open();
        }
    }

    open() {
        this.modal.open();
    }

    onClose() {
        const {setDetailedView} = this.props;
        setDetailedView(null);
    }

    render() {
        const {currentViewIndex, entries} = this.props;

        if (currentViewIndex === null) {
            return '';
        }
        const {description, html, userFullName, time} = entries[currentViewIndex];

        return (
            <Modal title={description}
                   ref={(ref) => {
                       this.modal = ref;
                   }}
                   onClose={this.onClose}
                   contentLabel="Details about log entry">
                <div>{userFullName}</div>
                <table className="i-table" dangerouslySetInnerHTML={{__html: html}} />
            </Modal>
        );
    }
}
