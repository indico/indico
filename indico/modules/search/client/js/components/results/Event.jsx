import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const Event = ({title, authors, startDate, endDate, location, link}) => (
  <>
    <List.Header>{title}</List.Header>
    <List.Description>
      <List>
        <List.Item>Authors: {authors.join(' ')}</List.Item>
        <List.Item>Start Date: {startDate}</List.Item>
        <List.Item>End Date: {endDate}</List.Item>
        <List.Item>Location: {location}</List.Item>
        <List.Item>
          <a href={link}>{link}</a>
        </List.Item>
      </List>
    </List.Description>
  </>
);

Event.propTypes = {
  title: PropTypes.string.isRequired,
  authors: PropTypes.arrayOf(PropTypes.string).isRequired,
  startDate: PropTypes.string.isRequired,
  endDate: PropTypes.string.isRequired,
  location: PropTypes.string.isRequired,
  link: PropTypes.string.isRequired,
};
export default Event;
