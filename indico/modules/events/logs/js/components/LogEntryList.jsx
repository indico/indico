import React from 'react';

export default class LogEntryList extends React.Component {
    render() {
        return (
            <div>
                {this.props.entries.map((item, index) => (
                    <div key={index}>{item.title}</div>
                ))}
            </div>
        );
    }
}
