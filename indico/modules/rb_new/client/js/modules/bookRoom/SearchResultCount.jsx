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
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {Icon, Label, Menu, Message, Popup} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import {actions as bookRoomActions} from '../../modules/bookRoom';
import * as selectors from './selectors';

import './BookRoom.module.scss';


class SearchResultCount extends React.Component {
    static propTypes = {
        isSearching: PropTypes.bool.isRequired,
        available: PropTypes.number,
        totalMatchingFilters: PropTypes.number,
        unbookable: PropTypes.number,
        actions: PropTypes.exact({
            openUnavailableRooms: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        available: null,
        totalMatchingFilters: null,
        unbookable: null,
    };

    renderRoomTotal(count) {
        const trigger = (
            <Menu.Item as="span">
                <Icon name="filter" />
                <Translate>
                    Total
                    <Param name="count"
                           value={<Label horizontal size="small">{count}</Label>} />
                </Translate>
            </Menu.Item>
        );
        return (
            <Popup trigger={trigger}>
                <Translate>
                    Number of spaces that match your filtering criteria.
                </Translate>
            </Popup>
        );
    }

    renderRoomAvailable(count) {
        const label = <Label color="teal" horizontal size="small">{count}</Label>;
        const trigger = (
            <Menu.Item active as="span">
                <Icon name="calendar alternate outline" />
                <Translate>
                    Available
                    <Param name="count"
                           value={label} />
                </Translate>
            </Menu.Item>
        );

        return (
            <Popup trigger={trigger}>
                <Translate>
                    Spaces that are free on that time slot.
                </Translate>
            </Popup>
        );
    }

    renderUnavailable(count) {
        const {actions: {openUnavailableRooms}} = this.props;
        const label = <Label color="red" horizontal size="small">{count}</Label>;
        const trigger = (
            <Menu.Item link onClick={openUnavailableRooms}>
                <Icon name="remove" />
                <Translate>
                    Unavailable
                    <Param name="count"
                           value={label} />
                </Translate>
            </Menu.Item>
        );
        return (
            <Popup trigger={trigger}>
                <Translate>
                    Spaces unavailable during that time slot (click for details).
                </Translate>
            </Popup>
        );
    }

    renderUnbookable(count) {
        const label = <Label color="red" horizontal size="small">{count}</Label>;
        const trigger = (
            <Menu.Item as="span">
                <Icon name="lock" />
                <Translate>
                    Unauthorized
                    <Param name="count" value={label} />
                </Translate>
            </Menu.Item>
        );
        return (
            <Popup trigger={trigger}>
                <Translate>
                    Spaces you are not authorized to book.
                </Translate>
            </Popup>
        );
    }

    renderNoRooms() {
        return (
            <Message icon="times circle outline"
                     error
                     content={Translate.string('No known spaces match your query')} />
        );
    }

    renderNoMatching() {
        return (
            <Message icon="warning sign"
                     warning
                     content={Translate.string('No spaces are available during that timeslot')}
                     styleName="message-nothing" />
        );
    }

    render() {
        const {isSearching, available, totalMatchingFilters, unbookable} = this.props;
        const unavailable = totalMatchingFilters - available - unbookable;
        const style = {
            display: (isSearching || (totalMatchingFilters > 0)) ? 'inline-flex' : 'none'
        };

        return (
            <div styleName="results-count">
                <Menu icon
                      styleName="results-count-menu"
                      className={isSearching ? 'loading' : null}
                      style={style}>
                    {isSearching ? (
                        <div styleName="loading-indicator">
                            <div className="bar" />
                            <div className="bar" />
                            <div className="bar" />
                        </div>
                    ) : (
                        !!totalMatchingFilters && (
                            <>
                                {this.renderRoomTotal(totalMatchingFilters)}
                                {this.renderRoomAvailable(available)}
                                {!!unavailable && this.renderUnavailable(unavailable)}
                                {!!unbookable && this.renderUnbookable(unbookable)}
                            </>
                        )
                    )}
                </Menu>
                {!isSearching && (
                    <>
                        {totalMatchingFilters > 0 && available === 0 && this.renderNoMatching()}
                        {totalMatchingFilters === 0 && this.renderNoRooms()}
                    </>
                )}
            </div>
        );
    }
}

export default connect(
    state => ({
        isSearching: selectors.isSearching(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            openUnavailableRooms: bookRoomActions.openUnavailableRooms,
        }, dispatch),
    }),
)(SearchResultCount);
