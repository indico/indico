import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const Contribution = ({title, authors, startDate, event}) => (
  <>
    <List.Header>{title}</List.Header>
    <List.Description>
      <List>
        <List.Item>Authors: {authors.join(' ')}</List.Item>
        <List.Item>Start Date: {startDate}</List.Item>
        <List.Item>Event: {event}</List.Item>
      </List>
    </List.Description>
  </>
);

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  authors: PropTypes.arrayOf(PropTypes.string).isRequired,
  startDate: PropTypes.string.isRequired,
  event: PropTypes.string.isRequired,
};
export default Contribution;
