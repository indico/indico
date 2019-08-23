import React, {useState} from 'react';
import {Pagination} from 'semantic-ui-react';

const SearchPagination = () => {
  const [activePage, setActivePage] = useState(1);
  const onChange = (e, pageInfo) => {
    setActivePage(pageInfo.activePage);
  };

  return (
    <Pagination
      activePage={activePage}
      onPageChange={onChange}
      firstItem={null}
      lastItem={null}
      pointing
      secondary
      totalPages={5}
    />
  );
};

export default SearchPagination;
