// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Message} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';

const NoResults = ({query}) => (
  <Message warning>
    <Message.Header>{Translate.string('No Results')}</Message.Header>
    {query ? (
      <Translate>
        Your search - <Param name="query" value={query} /> - did not match any results
      </Translate>
    ) : (
      <Translate>Please enter a term above to begin searching</Translate>
    )}
  </Message>
);

NoResults.propTypes = {
  query: PropTypes.string.isRequired,
};
export default NoResults;
