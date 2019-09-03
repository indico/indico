import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import moment from 'moment';

import './Contribution.module.scss';

const Contribution = ({title, url, startDt, persons}) => (
  <div styleName="contribution">
    <List.Header>
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      {persons.length !== 0 &&
        persons.map(item => (
          <List.Item key={item.id} styleName="high-priority">
            {item.title ? `${item.title} ${item.name}` : `${item.name}`}
          </List.Item>
        ))}
      <List.Item styleName="med-priority">
        {moment(startDt, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY HH:mm')}
      </List.Item>
    </List.Description>
  </div>
);

Contribution.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  startDt: PropTypes.string.isRequired,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
};
export default Contribution;
