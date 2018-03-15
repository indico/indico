import React from 'react';

import Toolbar from './Toolbar';
import LogEntryList from './LogEntryList';

export default class EventLog extends React.Component {
    render() {
        return <div>
            <Toolbar />
            <LogEntryList />
        </div>;
    }
}
