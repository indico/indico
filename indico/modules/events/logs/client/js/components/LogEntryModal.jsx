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

import {IButton, Modal} from 'indico/react/components';
import {Slot} from 'indico/react/util';


export default class LogEntryModal extends React.Component {
    static propTypes = {
        entries: PropTypes.array.isRequired,
        currentViewIndex: PropTypes.number,
        setDetailedView: PropTypes.func.isRequired,
        prevEntry: PropTypes.func.isRequired,
        nextEntry: PropTypes.func.isRequired
    };

    static defaultProps = {
        currentViewIndex: null
    };

    constructor(props) {
        super(props);
        this.modal = undefined;
        this.onClose = this.onClose.bind(this);
        this.prevEntry = this.prevEntry.bind(this);
        this.nextEntry = this.nextEntry.bind(this);
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

    prevEntry() {
        const {prevEntry} = this.props;
        prevEntry();
    }

    nextEntry() {
        const {nextEntry} = this.props;
        nextEntry();
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
                   contentLabel="Details about log entry"
                   fixedFooter>
                <Slot>
                    <table className="i-table log-modal-details" dangerouslySetInnerHTML={{__html: html}} />
                    <div className="text-superfluous log-modal-author-info flexrow f-j-end">
                        <span>
                            {userFullName && <span className="log-modal-user">{userFullName} </span>}
                            on
                            <span className="log-modal-time"> {moment(time).format('ddd, D/M/YYYY HH:mm')}</span>
                        </span>
                    </div>
                </Slot>
                <Slot name="footer">
                    <div className="group flexrow f-j-space-between">
                        <IButton title="Previous" icon="prev" onClick={this.prevEntry}>
                            Previous
                        </IButton>
                        <IButton title="Next" classes={{next: true}} highlight onClick={this.nextEntry}>
                            Next
                        </IButton>
                    </div>
                </Slot>
            </Modal>
        );
    }
}
