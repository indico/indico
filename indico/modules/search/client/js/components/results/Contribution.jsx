import React from 'react';
import {List, Icon} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import moment from 'moment';

import '../ResultList.module.scss';

const Contribution = ({title, authors, startDate, url}) => (
  <>
    <List.Header>
      <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
    </List.Header>
    <List.Description>
      <List>
        <List.Item>
          {authors.join(' ') && (
            <>
              <Icon name="pencil alternate" />
              {authors.join(', ')}{' '}
            </>
          )}
        </List.Item>
        <List.Item>
          <Icon name="calendar alternate outline" />
          {moment(startDate).format('DD/MM/YYYY')}
        </List.Item>
      </List>
    </List.Description>
  </>
);

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  authors: PropTypes.arrayOf(PropTypes.string).isRequired,
  startDate: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};
export default Contribution;
