import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import moment from 'moment';

import './Contribution.module.scss';

const Contribution = ({title, url, startDt, eventURL, eventTitle, persons}) => (
  <div styleName="contribution">
    <List.Header>
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      <a href={eventURL}>in Event {eventTitle}</a>
      {persons.length !== 0 && (
        <ul styleName="high-priority">
          {persons.map(item => (
            <li key={item.id}>{item.title ? `${item.title} ${item.name}` : `${item.name}`}</li>
          ))}
        </ul>
      )}
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
  eventURL: PropTypes.string.isRequired,
  eventTitle: PropTypes.string.isRequired,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
};
export default Contribution;
