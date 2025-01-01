// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Card, Container, Message} from 'semantic-ui-react';

import {StickyWithScrollBack} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import CardPlaceholder from '../../components/CardPlaceholder';

import * as blockingsActions from './actions';
import BlockingCard from './BlockingCard';
import BlockingFilterBar from './BlockingFilterBar';
import * as blockingsSelectors from './selectors';

import './BlockingList.module.scss';

class BlockingList extends React.Component {
  static propTypes = {
    blockings: PropTypes.object.isRequired,
    isFetching: PropTypes.bool.isRequired,
    filters: PropTypes.object.isRequired,
    actions: PropTypes.exact({
      fetchBlockings: PropTypes.func.isRequired,
      openBlockingDetails: PropTypes.func.isRequired,
    }).isRequired,
  };

  constructor(props) {
    super(props);
    this.contextRef = React.createRef();
  }

  componentDidMount() {
    const {
      actions: {fetchBlockings},
    } = this.props;
    fetchBlockings();
  }

  componentDidUpdate({filters: prevFilters}) {
    const {
      filters,
      actions: {fetchBlockings},
    } = this.props;
    if (prevFilters !== filters) {
      fetchBlockings();
    }
  }

  renderBlocking = blocking => {
    const {
      actions: {openBlockingDetails},
    } = this.props;
    return (
      <BlockingCard
        key={blocking.id}
        blocking={blocking}
        onClick={() => openBlockingDetails(blocking.id)}
      />
    );
  };

  renderContent = () => {
    const {isFetching, blockings} = this.props;
    const blockingsList = Object.values(blockings);

    if (isFetching) {
      return <CardPlaceholder.Group count={10} className="blockings-placeholders" />;
    } else if (blockingsList.length !== 0) {
      return (
        <Card.Group styleName="blockings-list">{blockingsList.map(this.renderBlocking)}</Card.Group>
      );
    } else {
      return (
        <Message info>
          <Translate>There are no blockings.</Translate>
        </Message>
      );
    }
  };

  render() {
    return (
      <div ref={this.contextRef}>
        <Container styleName="blockings-container" fluid>
          <StickyWithScrollBack context={this.contextRef.current}>
            <BlockingFilterBar />
          </StickyWithScrollBack>
          {this.renderContent()}
        </Container>
      </div>
    );
  }
}

export default connect(
  state => ({
    blockings: blockingsSelectors.getAllBlockings(state),
    isFetching: blockingsSelectors.isFetchingBlockings(state),
    filters: blockingsSelectors.getFilters(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        fetchBlockings: blockingsActions.fetchBlockings,
        openBlockingDetails: blockingsActions.openBlockingDetails,
      },
      dispatch
    ),
  })
)(BlockingList);
