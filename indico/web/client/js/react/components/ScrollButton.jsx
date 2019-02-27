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
import {Button, Popup} from 'semantic-ui-react';
import PropTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import './ScrollButton.module.scss';


export default function ScrollButton({visible}) {
    function scrollToTop() {
        window.scroll({left: 0, top: 0, behavior: 'smooth'});
    }

    return (
        <Popup trigger={<Button icon="angle up"
                                onClick={scrollToTop}
                                styleName={`scroll-btn ${visible ? 'visible' : ''}`} />}
               content={Translate.string('Back to top')} />
    );
}

ScrollButton.propTypes = {
    visible: PropTypes.bool.isRequired
};
