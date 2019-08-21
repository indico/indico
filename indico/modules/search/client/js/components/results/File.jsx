import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const File = ({title, authors, date, url}) => (
  <>
    <List.Header>
      <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
    </List.Header>
    <List.Description>
      <List>
        <List.Item>Authors: {authors.join(' ')}</List.Item>
        <List.Item>Date: {date}</List.Item>
      </List>
    </List.Description>
  </>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  authors: PropTypes.arrayOf(PropTypes.string).isRequired,
  date: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};
export default File;
