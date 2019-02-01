/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Icon, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import * as linkingActions from './actions';
import * as linkingSelectors from './selectors';

import './LinkBar.module.scss';


const messages = {
    event: Translate.string('Your booking will be linked to an event:'),
    contribution: Translate.string('Your booking will be linked to a contribution:'),
    sessionBlock: Translate.string('Your booking will be linked to a session block:'),
};

const LinkBar = ({visible, clear, data: {type, title, eventURL, eventTitle}}) => {
    if (!visible) {
        return null;
    }

    return (
        <header styleName="link-bar">
            <Icon name="info circle" />
            <span>
                {messages[type]}{' '}
                {type === 'event'
                    /* eslint-disable react/jsx-no-target-blank */
                    ? <a href={eventURL} target="_blank"><em>{title}</em></a>
                    : <span><em>{title}</em> (<a href={eventURL} target="_blank">{eventTitle}</a>)</span>
                }
            </span>
            <span styleName="clear" onClick={clear}>
                <Popup trigger={<Icon name="close" />}>
                    <Translate>
                        Exit linking mode
                    </Translate>
                </Popup>
            </span>
        </header>
    );
};

LinkBar.propTypes = {
    visible: PropTypes.bool.isRequired,
    clear: PropTypes.func.isRequired,
    data: PropTypes.shape({
        type: PropTypes.string,
        id: PropTypes.number,
        title: PropTypes.string,
        eventURL: PropTypes.string,
        eventTitle: PropTypes.string,
    }).isRequired,
};

export default connect(
    state => ({
        visible: linkingSelectors.hasLinkObject(state),
        data: linkingSelectors.getLinkObject(state),
    }),
    dispatch => ({
        clear: bindActionCreators(linkingActions.clearObject, dispatch),
    })
)(LinkBar);
