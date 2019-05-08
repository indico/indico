// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';


export default class TooltipIfTruncated extends React.Component {
    static propTypes = {
        children: PropTypes.any.isRequired
    };

    mouseEnter(event) {
        const element = event.target;
        const overflows = element.offsetWidth < element.scrollWidth || element.offsetHeight < element.scrollHeight;

        if (overflows && !element.getAttribute('title')) {
            element.setAttribute('title', element.innerText);
        }
    }

    render() {
        const {children} = this.props;
        const child = React.Children.only(children);
        return React.cloneElement(child, {onMouseEnter: (event) => this.mouseEnter(event)});
    }
}
