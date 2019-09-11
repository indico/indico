import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './Event.module.scss';
import moment from 'moment';
import CategoryPath from './CategoryPath';

const Event = ({
  // id,
  type,
  title,
  url,
  // description,
  categoryPath,
  startDt,
  endDt,
  // location,
  speakers,
  // chairs,
}) => {
  const singleDay =
    moment(startDt, 'YYYY-MM-DDZhh:mm').format('ll') ===
    moment(endDt, 'YYYY-MM-DDZhh:mm').format('ll');

  return (
    <div styleName="event">
      <List.Header>
        <a href={url}>{title}</a>
      </List.Header>
      <List.Description styleName="description">
        {/* if it's a lecture print the list of speakers */}
        {type === 'lecture' && speakers.length !== 0 && (
          <List.Item styleName="high-priority">
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
        {singleDay ? (
          <List.Item styleName="med-priority">
            {moment(startDt, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY HH:mm')}
          </List.Item>
        ) : (
          <List.Item styleName="med-priority">
            {`${moment(startDt, 'YYYY-MM-DDZhh:mm').format('DD MMMM')} -
              ${moment(endDt, 'YYYY-MM-DDZhh:mm').format('DD MMMM YYYY')}`}
          </List.Item>
        )}
        {/* Render the path */}
        {categoryPath.length !== 0 && (
          <List.Item>
            <div styleName="low-priority">
              <List.Description>
                <CategoryPath path={categoryPath} />
              </List.Description>
            </div>
          </List.Item>
        )}
      </List.Description>
    </div>
  );
};

Event.defaultProps = {
  speakers: [],
  // chairs: [],
};

const personShape = PropTypes.shape({
  title: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  affiliation: PropTypes.string.isRequired,
});

Event.propTypes = {
  // id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  type: PropTypes.oneOf(['lecture', 'meeting', 'conference']).isRequired,
  startDt: PropTypes.string.isRequired,
  endDt: PropTypes.string.isRequired,
  categoryPath: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
    })
  ).isRequired,
  // description: PropTypes.string.isRequired,
  // location: PropTypes.object.isRequired,
  speakers: PropTypes.arrayOf(personShape),
  // chairs: PropTypes.arrayOf(personShape),
};

export default Event;
