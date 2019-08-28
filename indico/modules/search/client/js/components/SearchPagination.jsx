import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Pagination} from 'semantic-ui-react';
import './SearchPagination.module.scss';

export default function SearchPagination({data, children}) {
  const recPerPage = 4;
  const [activePage, setActivePage] = useState(1);
  const [dataToShow, setDataToShow] = useState(data.slice(0, recPerPage));

  const found = data.some(r => dataToShow.indexOf(r) >= 0);

  if (!found) {
    setActivePage(1);
    setDataToShow(data.slice(0, recPerPage));
  }

  const onChange = (e, {activePage: active}) => {
    e.preventDefault();

    setActivePage(active);
    setDataToShow(data.slice((active - 1) * recPerPage, active * recPerPage));
  };

  const numOfPages = data => Math.ceil(data.length / recPerPage);

  return (
    <div>
      {children(dataToShow)}
      <div styleName="pagination">
        <Pagination
          activePage={activePage}
          onPageChange={onChange}
          totalPages={numOfPages(data)}
          boundaryRange={1}
          ellipsisItem={null}
          siblingRange={2}
          firstItem={null}
          lastItem={null}
        />
      </div>
    </div>
  );
}

SearchPagination.propTypes = {
  data: PropTypes.array.isRequired,
  children: PropTypes.func.isRequired,
};
