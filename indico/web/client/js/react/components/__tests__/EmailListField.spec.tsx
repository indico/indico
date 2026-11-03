// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mount} from 'enzyme';
import React from 'react';
import {act} from 'react-dom/test-utils';
import {Dropdown} from 'semantic-ui-react';

import {EmailListField} from '../EmailListField';
import TagListField from '../TagListField';

describe('EmailListField', () => {
  it.each(['selection', 'paste'])(
    'lowercases and deduplicates addresses added through %s',
    method => {
      const value = ['FIRST@EXAMPLE.ORG', 'first@example.org'];
      const onChange = jest.fn();
      const field = mount(<EmailListField value={value} onChange={onChange} />).find(TagListField);
      const address = 'SECOND@EXAMPLE.ORG';

      if (method === 'selection') {
        act(() => {
          field.find(Dropdown).prop('onChange')(null, {value: [...value, address]});
        });
      } else {
        act(() => {
          field.find(Dropdown).prop('onSearchChange')(null, {
            searchQuery: method === 'paste' ? `${address};` : address,
          });
        });
      }

      expect(onChange).toHaveBeenCalledWith(['first@example.org', 'second@example.org']);
    }
  );
});
