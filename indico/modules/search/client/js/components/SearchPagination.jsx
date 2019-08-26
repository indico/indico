import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {List, Pagination} from 'semantic-ui-react';
import './ResultList.module.scss';

export default function SearchPagination({component: Component, data}) {
  const recPerPage = 5;
  const [activePage, setActivePage] = useState(1);
  const [arrayStart, setArrayStart] = useState(0);
  const [arrayEnd, setArrayEnd] = useState(recPerPage);
  const [dataToShow, setDataToShow] = useState(data.slice(arrayStart, arrayEnd));

  const onChange = (e, pageInfo) => {
    e.preventDefault();
    e.persist();
    setActivePage(pageInfo.activePage);
    console.log('activepage ==== ', activePage);
    setArrayStart(Math.max(activePage - 1, 0) * recPerPage);
    setArrayEnd(arrayStart + recPerPage);
    setDataToShow(data.slice(arrayStart, arrayEnd));
    console.log(
      'activepage:',
      activePage,
      'first:',
      arrayStart,
      'last:',
      arrayEnd,
      'data::',
      dataToShow
    );
  };
  const numOfPages = data => Math.ceil(data.length / recPerPage);

  return (
    <div>
      <List divided relaxed>
        {dataToShow.map(item => (
          <List.Item key={item.url}>
            <List.Content styleName="list">
              <Component {...item} />
            </List.Content>
          </List.Item>
        ))}
      </List>
      <Pagination
        activePage={activePage}
        onPageChange={onChange}
        // firstItem={firstItem}
        // lastItem={lastItem}
        totalPages={numOfPages(data)}
        boundaryRange={0}
        ellipsisItem={null}
        siblingRange={1}
      />
    </div>
  );
}

SearchPagination.propTypes = {
  component: PropTypes.elementType.isRequired,
  data: PropTypes.array.isRequired,
};
