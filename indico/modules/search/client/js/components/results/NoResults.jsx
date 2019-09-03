import React from 'react';
import {Message} from 'semantic-ui-react';
import './NoResults.module.scss';

const NoResults = () => (
  <div styleName="no-results">
    <Message negative>
      <Message.Header>No Results</Message.Header>
      <p>We couldn't fetch any results</p>
    </Message>
  </div>
);

export default NoResults;
