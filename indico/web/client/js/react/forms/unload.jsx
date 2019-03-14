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

import React, {useEffect} from 'react';
import PropTypes from 'prop-types';
import {Prompt} from 'react-router';
import {Translate} from '../../react/i18n';


const UnloadPrompt = ({active, router, message}) => {
    if (!message) {
        message = Translate.string('Are you sure you want to leave this page without saving?');
    }

    useEffect(() => {
        if (!active) {
            return;
        }

        const onBeforeUnload = e => {
            e.preventDefault();
            e.returnValue = message;
        };

        window.addEventListener('beforeunload', onBeforeUnload);
        return () => {
            window.removeEventListener('beforeunload', onBeforeUnload);
        };
    }, [active, message]);

    return router ? <Prompt when={active} message={message} /> : null;
};

UnloadPrompt.propTypes = {
    active: PropTypes.bool.isRequired,
    router: PropTypes.bool,
    message: PropTypes.string,
};

UnloadPrompt.defaultProps = {
    message: null,
    router: true,
};


export default React.memo(UnloadPrompt);
