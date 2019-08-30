import React from 'react';
import {List, Breadcrumb} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './Event.module.scss';

import moment from 'moment';

const Event = ({
  id,
  event_type,
  title,
  URL,
  description,
  category_path,
  start_dt,
  end_dt,
  location,
  speakers,
  chairs,
}) => {
  const singleDay =
    moment(start_dt, 'YYYY-MM-DDZhh:mm').format('ll') ===
    moment(end_dt, 'YYYY-MM-DDZhh:mm').format('ll');
  const multipleDays = !singleDay;
  const array = category_path.slice(0, category_path.length - 1);

  return (
    <div styleName="event">
      <List.Header>
        <a href={URL}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        {/* if it's a lecture print the list of speakers */}
        {event_type === 'lecture' && speakers.length !== 0 && (
          <List.Item styleName="high_priority">
            {speakers.map(i => (
              <div key={i.name}>
                {i.title
                  ? `${i.title} ${i.name} (${i.affiliation})`
                  : `${i.name} (${i.affiliation})`}
              </div>
            ))}
          </List.Item>
        )}

        {/* Dates */}
        {/* if end date == start date only show start date */}
        {singleDay && (
          <List.Item styleName="med_priority">
            {moment(start_dt, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY HH:mm')}
          </List.Item>
        )}
        {multipleDays && (
          <List.Item styleName="med_priority">
            {`${moment(start_dt, 'YYYY-MM-DDZhh:mm').format('DD MMMM')} -
              ${moment(end_dt, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY')}`}
          </List.Item>
        )}
        {/* Render the path */}
        <List.Item>
          <Breadcrumb styleName="low_priority">
            {array.map(item => (
              <Breadcrumb.Section key={item}>
                <a href={item[1]}>
                  {item[0]}
                  <span>&nbsp;</span>
                </a>
                {' » '}
                <span>&nbsp;</span>
              </Breadcrumb.Section>
            ))}
            <Breadcrumb.Section active>
              <a href={category_path[category_path.length - 1][1]}>
                {category_path[category_path.length - 1][0]}
                <span>&nbsp;</span>
              </a>
            </Breadcrumb.Section>
          </Breadcrumb>
        </List.Item>
      </List.Description>
    </div>
  );
};

Event.defaultProps = {
  speakers: [],
  chairs: [],
};

Event.propTypes = {
  id: PropTypes.string.isRequired,
  event_type: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  URL: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  category_path: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)).isRequired,
  start_dt: PropTypes.string.isRequired,
  end_dt: PropTypes.string.isRequired,
  location: PropTypes.object.isRequired,
  speakers: PropTypes.arrayOf(PropTypes.object),
  chairs: PropTypes.arrayOf(PropTypes.object),
};

export default Event;
