import React from 'react';
import { connect } from 'react-redux';

export class Toolbar extends React.Component {
    render() {
        return 'Toolbar goes here';
    }
}

Toolbar = connect()(Toolbar)
export default Toolbar;
