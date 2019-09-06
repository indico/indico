import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './File.module.scss';
import moment from 'moment';

const File = ({title, url, date, persons}) => (
  <div styleName="file">
    <List.Header>
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      {persons.length !== 0 && (
        <div styleName="high-priority">
          {persons.map(item => (
            <li key={item.id}>{item.title ? `${item.title} ${item.name}` : `${item.name}`}</li>
          ))}
        </div>
      )}
      <List.Item styleName="med-priority">
        {moment(date, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY HH:mm')}
      </List.Item>
    </List.Description>
  </div>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  date: PropTypes.string.isRequired,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
};
export default File;
