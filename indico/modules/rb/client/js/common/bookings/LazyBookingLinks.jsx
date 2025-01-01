// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getBookingLinksDataURL from 'indico-url:rb.booking_links_data';

import PropTypes from 'prop-types';
import React from 'react';
import {Placeholder, Segment} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';

import BookingLinks from './BookingLinks';

/**
 * `LazyBookingLinks` wraps `BookingLinks` and loads the data of the links on demand.
 */
export default function LazyBookingLinks({id}) {
  const {data, loading} = useIndicoAxios(getBookingLinksDataURL({booking_id: id}), {
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

  return <BookingLinks links={data} />;
}

LazyBookingLinks.propTypes = {
  id: PropTypes.number.isRequired,
};
