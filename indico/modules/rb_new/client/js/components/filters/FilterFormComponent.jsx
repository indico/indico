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

/* eslint "react/no-unused-prop-types": "off" */


import React from 'react';
import propTypes from 'prop-types';


export default class FilterFormBase extends React.Component {
    static propTypes = {
        setParentField: propTypes.func.isRequired
    };

    static getDerivedStateFromProps(props, prevState) {
        // override internal state from props.
        // this allows other widgets and reducers to perform
        // corrections which will be reflected next time the
        // component is rendered
        return {...prevState, ...props};
    }

    constructor(props) {
        super(props);
        this.state = {};
    }
}
