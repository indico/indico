// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {shallow} from 'enzyme';
import React from 'react';
import {Dropdown, Input} from 'semantic-ui-react';

import ListFilter from '../ListFilter';

const list = [
  {id: 12, text: 'Science-Lab'},
  {id: 123, text: 'Science Lab'},
  {id: 3, text: 'ScienceLab'},
  {id: 4, text: 'Science annual Lab'},
];

describe('ListFilter', () => {
  it.each([
    'Science-Lab',
    'Science Lab',
    'ScienceLab',
    '  science\t lab  ',
    'Science—Lab',
    'Science/Lab',
  ])('matches punctuation and whitespace variants of %s', search => {
    const onChangeList = jest.fn();
    const field = shallow(
      <ListFilter
        list={list}
        filterOptions={[]}
        searchableFields={entry => [entry.text]}
        onChangeList={onChangeList}
      />
    );
    field.find(Input).simulate('change', {}, {value: search});
    expect(onChangeList).toHaveBeenLastCalledWith(new Set([12, 123, 3]));
  });

  it.each([
    ['#12', [12]],
    ['  #12  ', [12]],
    ['#999', []],
    ['Scinece Lab', []],
    ['Lab Science', []],
    ['', [12, 123, 3, 4]],
    [' \t ', [12, 123, 3, 4]],
  ])('preserves exact IDs and substring matching for %s', (search, ids) => {
    const onChangeList = jest.fn();
    const field = shallow(
      <ListFilter
        list={list}
        filterOptions={[]}
        searchableId={entry => entry.id}
        searchableFields={entry => [entry.text]}
        onChangeList={onChangeList}
      />
    );
    field.find(Input).simulate('change', {}, {value: search});
    expect(onChangeList).toHaveBeenLastCalledWith(new Set(ids));
  });

  it.each(['  Science Lab  ', '  #12  '])(
    'keeps the search active when filters change for %s',
    search => {
      const onChangeList = jest.fn();
      const field = shallow(
        <ListFilter
          list={list}
          filterOptions={[
            {
              key: 'session',
              text: 'Session',
              options: [{value: 'selected', text: 'Selected'}],
              isMatch: entry => entry.id !== 3,
            },
          ]}
          searchableId={entry => entry.id}
          searchableFields={entry => [entry.text]}
          onChangeList={onChangeList}
        />
      );
      field.find(Input).simulate('change', {}, {value: search});
      field.find(Dropdown).at(1).simulate('open');
      field
        .find(Dropdown.Item)
        .filterWhere(item => item.prop('value') === 'selected')
        .simulate('click', {}, {value: 'selected'});
      expect(onChangeList).toHaveBeenLastCalledWith(
        new Set(search.includes('#') ? [12] : [12, 123])
      );
    }
  );

  it('normalizes option searches', () => {
    const field = shallow(
      <ListFilter
        list={[]}
        filterOptions={[
          {
            key: 'session',
            text: 'Session',
            options: Array.from({length: 11}, (_, id) => ({
              value: String(id),
              text: 'Science-Lab',
            })),
          },
        ]}
      />
    );
    field.find(Dropdown).at(1).simulate('open');
    field.find(Input).at(0).simulate('change', {}, {value: 'science lab'});
    expect(
      field.find(Dropdown.Item).filterWhere(item => item.prop('text') === 'Science-Lab')
    ).toHaveLength(11);
  });
});
