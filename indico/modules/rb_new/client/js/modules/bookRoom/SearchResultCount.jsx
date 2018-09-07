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
import {Icon, Label, Menu, Message, Popup} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';

import './BookRoom.module.scss';


export default class SearchResultCount extends React.Component {
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
                    Number of rooms matching your filtering criteria
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
                    Rooms that are free on that time slot. Click for more details
                </Translate>
            </Popup>
        );
    }

    renderUnavailable(count) {
        const label = <Label color="red" horizontal size="small">{count}</Label>;
        const trigger = (
            <Menu.Item link>
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
                Rooms unavailable during that time slot
                </Translate>
            </Popup>
        );
    }

    renderNoRooms() {
        return (
            <Message icon="times circle outline"
                     error
                     content={Translate.string('No rooms match your query')} />
        );
    }

    renderNoMatching() {
        return (
            <Message icon="warning sign"
                     warning
                     content={Translate.string('No rooms are available during that timeslot')} />
        );
    }

    render() {
        const {isFetching, matching, total} = this.props;
        const style = {
            display: (isFetching || (total > 0)) ? 'inline-flex' : 'none'
        };

        return (
            <div styleName="results-count">
                <Menu icon
                      styleName="results-count-menu"
                      className={isFetching ? 'loading' : null}
                      style={style}>
                    {isFetching ? (
                        <div styleName="loading-indicator">
                            <div className="bar" />
                            <div className="bar" />
                            <div className="bar" />
                        </div>
                    ) : (
                        !!total && (
                            <>
                                {this.renderRoomTotal(total)}
                                {this.renderRoomAvailable(matching)}
                                {(matching < total) && this.renderUnavailable(total - matching)}
                            </>
                        )
                    )}
                </Menu>
                {!isFetching && (
                    <>
                        {total > 0 && matching === 0 && this.renderNoMatching()}
                        {total === 0 && this.renderNoRooms()}
                    </>
                )}
            </div>
        );
    }
}


SearchResultCount.propTypes = {
    isFetching: PropTypes.bool.isRequired,
    matching: PropTypes.number,
    total: PropTypes.number
};

SearchResultCount.defaultProps = {
    matching: null,
    total: null
};
