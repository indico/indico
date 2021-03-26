// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Pagination} from 'semantic-ui-react';
import './SearchPagination.module.scss';

// TODO: consider getting rid of such a simple wrapper
export default function SearchPagination({activePage, numOfPages, onPageChange}) {
  const handlePageChange = (e, {activePage: active}) => {
    onPageChange(active);
  };

  return (
    <div styleName="pagination">
      <Pagination
        activePage={activePage}
        onPageChange={handlePageChange}
        totalPages={numOfPages}
        boundaryRange={1}
        siblingRange={2}
      />
    </div>
  );
}

SearchPagination.propTypes = {
  activePage: PropTypes.number.isRequired,
  numOfPages: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired,
};
