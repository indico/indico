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

import _ from 'lodash';
import qs from 'qs';
import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Dimmer, Loader} from 'semantic-ui-react';
import {push} from 'connected-react-router';

import {Preloader} from 'indico/react/util';
import {actions as roomsActions, selectors as roomsSelectors} from '../common/rooms';
import RoomDetailsModal from '../components/modals/RoomDetailsModal';
import * as globalSelectors from '../selectors';
import * as modalActions from './actions';


class ModalController extends React.PureComponent {
    static propTypes = {
        isInitializing: PropTypes.bool.isRequired,
        path: PropTypes.string.isRequired,
        queryString: PropTypes.string.isRequired,
        actions: PropTypes.exact({
            pushState: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
            openBookRoom: PropTypes.func.isRequired,
        }).isRequired,
    };

    getQueryData() {
        const {queryString} = this.props;
        let {modal: modalData} = qs.parse(queryString);
        if (!modalData) {
            return [];
        }
        if (!Array.isArray(modalData)) {
            modalData = [modalData];
        }
        return _.uniq(modalData).map(data => [data.split(':', 2), data]);
    }

    getQueryStringWithout(arg) {
        const {queryString} = this.props;
        const params = qs.parse(queryString);
        if (Array.isArray(params.modal)) {
            params.modal = params.modal.filter(x => x !== arg);
        } else if (params.modal === arg) {
            delete params.modal;
        }
        return qs.stringify(params, {arrayFormat: 'repeat'});
    }

    makeCloseHandler(qsArg) {
        const {actions: {pushState}, path} = this.props;
        return () => {
            const queryString = this.getQueryStringWithout(qsArg);
            pushState(path + (queryString ? `?${queryString}` : ''));
        };
    }

    renderRoomDetails(roomId, onClose) {
        const {actions: {fetchRoomDetails, openBookRoom}} = this.props;
        const key = `roomDetails-${roomId}`;
        return (
            <Preloader checkCached={state => roomsSelectors.hasDetails(state, {roomId})}
                       action={() => fetchRoomDetails(roomId)}
                       dimmer={<Dimmer active page><Loader /></Dimmer>}
                       key={key}>
                {() => (
                    <RoomDetailsModal roomId={roomId}
                                      onClose={onClose}
                                      onBook={openBookRoom} />
                )}
            </Preloader>
        );
    }

    render() {
        const {isInitializing} = this.props;
        if (isInitializing) {
            return null;
        }
        return this.getQueryData().map(([[name, value], orig]) => {
            if (name === 'room-details') {
                return this.renderRoomDetails(value, this.makeCloseHandler(orig));
            } else {
                return null;
            }
        });
    }
}

export default connect(
    state => ({
        isInitializing: globalSelectors.isInitializing(state),
        path: state.router.location.pathname,
        queryString: state.router.location.search.substr(1),
    }),
    dispatch => ({
        actions: bindActionCreators({
            pushState: push,
            fetchRoomDetails: roomsActions.fetchDetails,
            openBookRoom: modalActions.openBookRoom,
        }, dispatch),
    }),
)(ModalController);
