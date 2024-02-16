// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getLinkedObjectDataURL from 'indico-url:rb.linked_object_data';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Placeholder, Segment} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';

import BookingObjectLink from './BookingObjectLink';

/**
 * `LazyBookingObjectLink` wraps `BookingObjectLink` and loads the data
 * of the object on demand.
 */
export default function LazyBookingObjectLink({type, id, pending}) {
  const {data, loading} = useIndicoAxios(getLinkedObjectDataURL({type: _.snakeCase(type), id}), {
    camelize: true,
  });

  if (loading) {
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
  } else if (!data) {
    // first render or error
    return null;
  }

  const {canAccess, ...rest} = data;
  const link = canAccess ? {type, ...rest} : null;
  return canAccess ? <BookingObjectLink pending={pending} link={link} /> : null;
}

LazyBookingObjectLink.propTypes = {
  type: PropTypes.oneOf(['event', 'contribution', 'sessionBlock']).isRequired,
  id: PropTypes.number.isRequired,
  /** Whether it is a pending link or the booking is already linked */
  pending: PropTypes.bool,
};

LazyBookingObjectLink.defaultProps = {
  pending: false,
};
