// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {shallow} from 'enzyme';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {EmailListField} from '../EmailListField';

describe('EmailListField', () => {
  it.each(['selection', 'paste', 'blur'])(
    'lowercases and deduplicates addresses added through %s',
    method => {
      const value = ['FIRST@EXAMPLE.ORG', 'first@example.org'];
      const onChange = jest.fn();
      const field = shallow(<EmailListField value={value} onChange={onChange} />);
      const address = 'SECOND@EXAMPLE.ORG';

      if (method === 'selection') {
        field.find(Dropdown).simulate('change', {}, {value: [...value, address]});
      } else {
        field.find(Dropdown).simulate(
          'searchChange',
          {},
          {
            searchQuery: method === 'paste' ? `${address};` : address,
          }
        );
        if (method === 'blur') {
          field.find(Dropdown).simulate('blur');
        }
      }

      expect(onChange).toHaveBeenCalledWith(['first@example.org', 'second@example.org']);
    }
  );
});
