import React from 'react';
import {List, Icon} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import '../ResultList.module.scss';
import moment from 'moment';

const File = ({title, authors, date, url}) => (
  <>
    <List.Header>
      <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
    </List.Header>
    <List.Description>
      <List>
        {authors.join(' ') && (
          <List.Item>
            <Icon name="pencil alternate" />
            {authors.join(', ')}{' '}
          </List.Item>
        )}

        <List.Item>
          <Icon name="calendar alternate outline" />
          {moment(date).format('DD/MM/YYYY')}
        </List.Item>
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
