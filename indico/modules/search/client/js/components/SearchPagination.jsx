import React from 'react';
import PropTypes from 'prop-types';
import {Pagination} from 'semantic-ui-react';
import './SearchPagination.module.scss';

export default function SearchPagination({activePage, numOfPages, onPageChange}) {
  const handlePageChange = (e, {activePage: active}) => {
    e.preventDefault();
    onPageChange(active);
  };

  return (
    <div styleName="pagination">
      <Pagination
        activePage={activePage}
        onPageChange={handlePageChange}
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
  onPageChange: PropTypes.func.isRequired,
};
