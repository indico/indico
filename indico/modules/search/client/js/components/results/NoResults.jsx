import React from 'react';
import PropTypes from 'prop-types';
import {Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

const NoResults = ({query}) => (
  <Message warning>
    <Message.Header>{Translate.string('No Results')}</Message.Header>
    {Translate.string(`Your search - ${query} - did not match any results`)}
  </Message>
);

NoResults.propTypes = {
  query: PropTypes.string.isRequired,
};
export default NoResults;
