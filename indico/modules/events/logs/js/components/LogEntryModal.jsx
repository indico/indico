import React from 'react';
import PropTypes from 'prop-types';

import Modal from 'indico/react/components/Modal';

export default class LogEntryModal extends React.Component {
    static propTypes = {
        entry: PropTypes.object,
        setDetailedView: PropTypes.func.isRequired
    };

    static defaultProps = {
        entry: null
    }

    constructor(props) {
        super(props);
        this.modal = undefined;
        this.onClose = this.onClose.bind(this);
    }

    componentDidUpdate() {
        const {entry} = this.props;
        if (entry) {
            this.open();
        }
    }

    open() {
        this.modal.open();
    }

    onClose() {
        const {setDetailedView} = this.props;
        setDetailedView(null);
    }

    render() {
        const {entry} = this.props;

        if (!entry) {
            return '';
        }

        const {description, html, userFullName} = entry;

        return (
            <Modal title={description}
                   ref={(ref) => {
                       this.modal = ref;
                   }}
                   onClose={this.onClose}
                   contentLabel="Details about log entry">
                <div>{userFullName}</div>
                <table className="i-table" dangerouslySetInnerHTML={{__html: html}} />
            </Modal>
        );
    }
}
