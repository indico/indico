import React from 'react';
import PropTypes from 'prop-types';
import {Message} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';

const NoResults = ({query}) => (
  <Message warning>
    <Message.Header>{Translate.string('No Results')}</Message.Header>
    <Translate>
      Your search - <Param name="query" value={query} /> - did not match any results
    </Translate>
  </Message>
);

NoResults.propTypes = {
  query: PropTypes.string.isRequired,
};
export default NoResults;
