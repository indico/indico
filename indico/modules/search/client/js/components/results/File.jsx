import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const File = ({title, authors, date}) => (
  <>
    <List.Header>{title}</List.Header>
    <List.Description>
      <List>
        <List.Item>Authors: {authors.join(' ')}</List.Item>
        <List.Item>Event Date: {date}</List.Item>
      </List>
    </List.Description>
  </>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  authors: PropTypes.arrayOf(PropTypes.string).isRequired,
  date: PropTypes.string.isRequired,
};
export default File;
