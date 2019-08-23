import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import '../ResultList.module.scss';

const Contribution = ({title, authors, startDate, event, url}) => (
  <>
    <List.Header>
      <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
    </List.Header>
    <List.Description>
      <List>
        <List.Item>{authors.join(' ')}</List.Item>
        <List.Item>{startDate}</List.Item>
        <List.Item>{event}</List.Item>
      </List>
    </List.Description>
  </>
);

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  authors: PropTypes.arrayOf(PropTypes.string).isRequired,
  startDate: PropTypes.string.isRequired,
  event: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};
export default Contribution;
