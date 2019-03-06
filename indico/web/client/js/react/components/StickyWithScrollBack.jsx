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

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Sticky} from 'semantic-ui-react';

import {ScrollButton} from 'indico/react/components';

import './StickyWithScrollBack.module.scss';


export default function StickyWithScrollBack({children, context}) {
    const [scrollButtonVisible, setScrollButtonVisible] = useState(false);

    return (
        <Sticky context={context} styleName="sticky-content"
                onStick={() => setScrollButtonVisible(true)}
                onUnstick={() => setScrollButtonVisible(false)}>
            {children}
            <ScrollButton visible={scrollButtonVisible} />
        </Sticky>
    );
}

StickyWithScrollBack.propTypes = {
    children: PropTypes.node,
    context: PropTypes.object,
};

StickyWithScrollBack.defaultProps = {
    children: null,
    context: null,
};
