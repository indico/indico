import React from 'react';
import {List, Icon} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './File.module.scss';
import moment from 'moment';

const iconSelector = type => {
  switch (type) {
    case 'file-word':
      return {color: 'blue', name: 'file word outline'};
    case 'file-zip':
      return {color: 'yellow', name: 'file archive outline'};
    case 'file-presentation':
      return {color: 'red', name: 'file powerpoint outline'};
    case 'file-excel':
      return {color: 'green', name: 'file excel outline'};
    case 'file-pdf':
      return {color: 'red', name: 'file pdf outline'};
    // case 'file-xml':
    //   return {name: 'file code outline'};
    case 'file-spreadsheet':
      return {color: 'green', name: 'file excel outline'};
    default:
      return {name: 'file outline'};
  }
};

const File = ({title, url, type, contributionTitle, date, contribURL, persons}) => (
  <div styleName="file">
    <List.Header>
      <Icon {...iconSelector(type)} />
      <a href={url}>{title}</a>
    </List.Header>
    <List.Description styleName="description">
      <List.Item styleName="high-priority">
        {'in Contribution '}
        <a href={contribURL}>{contributionTitle}</a>
      </List.Item>
      <List.Item>
        {persons.length !== 0 && (
          <ul styleName="high-priority">
            {'by '}
            {persons.map(item => (
              <li key={item.id}>{item.title ? `${item.title} ${item.name}` : `${item.name}`}</li>
            ))}
          </ul>
        )}
      </List.Item>
      <List.Item styleName="med-priority">
        {moment(date, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY HH:mm')}
      </List.Item>
    </List.Description>
  </div>
);

File.propTypes = {
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  contributionTitle: PropTypes.string.isRequired,
  date: PropTypes.string.isRequired,
  contribURL: PropTypes.string.isRequired,
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,
};
export default File;
