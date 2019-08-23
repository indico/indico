import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import '../ResultList.module.scss';

const Event = ({title, authors, startDate, endDate, location, url}) => (
  <>
    <List.Header>
      <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
    </List.Header>
    <List.Description>
      <List>
        <List.Item>{authors.join(' ')}</List.Item>
        <List.Item>{startDate}</List.Item>
        <List.Item>{endDate}</List.Item>
        <List.Item>{location}</List.Item>
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
  url: PropTypes.string.isRequired,
};
export default Event;
