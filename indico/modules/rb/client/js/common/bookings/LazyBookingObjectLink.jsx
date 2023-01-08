// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getLinkedObjectDataURL from 'indico-url:rb.linked_object_data';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Placeholder, Segment} from 'semantic-ui-react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import BookingObjectLink from './BookingObjectLink';

/**
 * `LazyBookingObjectLink` wraps `BookingObjectLink` and loads the data
 * of the object on demand.
 */
export default class LazyBookingObjectLink extends React.PureComponent {
  static propTypes = {
    type: PropTypes.oneOf(['event', 'contribution', 'sessionBlock']).isRequired,
    id: PropTypes.number.isRequired,
    /** Whether it is a pending link or the booking is already linked */
    pending: PropTypes.bool,
  };

  static defaultProps = {
    pending: false,
  };

  state = {
    loaded: false,
    link: {},
    canAccess: false,
  };

  componentDidMount() {
    const {type, id} = this.props;
    this.fetchLinkedObjectData(type, id);
  }

  async fetchLinkedObjectData(type, id) {
    let response;
    try {
      response = await indicoAxios.get(getLinkedObjectDataURL({type: _.snakeCase(type), id}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    const {canAccess, ...data} = camelizeKeys(response.data);
    this.setState({
      loaded: true,
      link: canAccess ? {type, ...data} : null,
      canAccess,
    });
  }

  render() {
    const {pending} = this.props;
    const {loaded, link, canAccess} = this.state;
    if (loaded && !canAccess) {
      return null;
    } else if (loaded) {
      return <BookingObjectLink pending={pending} link={link} />;
    } else {
      return (
        <Segment>
          <Placeholder fluid>
            <Placeholder.Header image>
              <Placeholder.Line length="full" />
              <Placeholder.Line length="full" />
            </Placeholder.Header>
          </Placeholder>
        </Segment>
      );
    }
  }
}
