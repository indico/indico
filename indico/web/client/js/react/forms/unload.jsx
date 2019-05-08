// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
