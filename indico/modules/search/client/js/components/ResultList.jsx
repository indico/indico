// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState, useEffect} from 'react';
import {List, Segment} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './ResultList.module.scss';
import SearchPagination from './SearchPagination';

export default function ResultList({component: Component, allData}) {
  // const data = datasetSelector(Component.name);
  const recPerPage = 7;
  const [dataToShow, setDataToShow] = useState(allData.slice(0, recPerPage));
  const [activePage, setActivePage] = useState(1);
  const numOfPages = allData.length / recPerPage;

  useEffect(() => {
    setDataToShow(allData.slice((activePage - 1) * recPerPage, activePage * recPerPage));
  }, [activePage, allData]);

  return (
    <>
      <Segment>
        <List divided relaxed>
          {dataToShow.map(item => (
            <List.Item key={item.url}>
              <List.Content styleName="list">
                <Component {...item} />
              </List.Content>
            </List.Item>
          ))}
        </List>
      </Segment>
      {numOfPages !== 1 && (
        <SearchPagination
          activePage={activePage}
          numOfPages={numOfPages}
          setActivePage={setActivePage}
        />
      )}
    </>
  );
}

ResultList.propTypes = {
  component: PropTypes.elementType.isRequired,
  allData: PropTypes.array.isRequired,
};

// also fix the descriptions in events and files to be more user friendly
