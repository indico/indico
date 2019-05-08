// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
