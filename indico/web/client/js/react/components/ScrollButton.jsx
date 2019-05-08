// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
