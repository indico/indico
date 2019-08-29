import React from 'react';
import PropTypes from 'prop-types';
import {Pagination} from 'semantic-ui-react';
import './SearchPagination.module.scss';

export default function SearchPagination({activePage, numOfPages, setActivePage}) {
  const onChange = (e, {activePage: active}) => {
    e.preventDefault();
    setActivePage(active);
  };

  return (
    <div styleName="pagination">
      <Pagination
        activePage={activePage}
        onPageChange={onChange}
        totalPages={numOfPages}
        boundaryRange={1}
        ellipsisItem={null}
        siblingRange={2}
        firstItem={null}
        lastItem={null}
      />
    </div>
  );
}

SearchPagination.propTypes = {
  activePage: PropTypes.number.isRequired,
  numOfPages: PropTypes.number.isRequired,
  setActivePage: PropTypes.func.isRequired,
};
