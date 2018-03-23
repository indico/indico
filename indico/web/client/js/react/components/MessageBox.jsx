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


export default class MessageBox extends React.Component {
    static propTypes = {
        type: PropTypes.oneOf(['info', 'highlight', 'error', 'danger', 'warning', 'success']).isRequired,
        icon: PropTypes.bool,
        fixedWidth: PropTypes.bool,
        largeIcon: PropTypes.bool,
        children: PropTypes.any.isRequired
    };

    static defaultProps = {
        icon: true,
        fixedWidth: false,
        largeIcon: false,
    };

    render() {
        const {type, icon, fixedWidth, largeIcon, children} = this.props;
        return (
            <div className={`${type}-message-box ${fixedWidth ? 'fixed-width' : ''} ${largeIcon ? 'large-icon' : ''}`}>
                <div className="message-box-content">
                    {icon && <span className="icon" />}
                    <div className="message-text">
                        {children}
                    </div>
                </div>
            </div>
        );
    }
}
