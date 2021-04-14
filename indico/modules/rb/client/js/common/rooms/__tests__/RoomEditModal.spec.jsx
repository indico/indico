// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import attributesURL from 'indico-url:rb.admin_attributes';
import permissionInfoURL from 'indico-url:rb.permission_types';

import {mount} from 'enzyme';
import axiosMock from 'jest-mock-axios';
import React from 'react';
import {act} from 'react-dom/test-utils';
import {FieldArray} from 'react-final-form-arrays';
import {Provider} from 'react-redux';
import configureMockStore from 'redux-mock-store';
import {Tab} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';

import RoomEditModal from '../edit/RoomEditModal';

jest.mock('indico/react/components/principals/ACLField', () => () => null);

describe('RoomEditModal', () => {
  const mockStore = configureMockStore();

  it('should contain fields matching the respective Tab pane', () => {
    const initialState = {
      rooms: {
        equipmentTypes: [],
      },
    };
    const store = mockStore(initialState);
    const component = mount(
      <Provider store={store}>
        <RoomEditModal onClose={() => {}} />
      </Provider>
    );
    act(() => {
      axiosMock.mockResponseFor({url: permissionInfoURL()}, {data: {tree: {}, default: ''}});
      axiosMock.mockResponseFor({url: attributesURL()}, {data: [{name: 'foo', value: 'bar'}]});
    });
    component.update();
    const tabCmp = component.find(Tab);
    expect(tabCmp).toBeDefined();

    for (const pane of tabCmp.prop('panes')) {
      expect(pane).toHaveProperty('pane');
      expect(pane).toHaveProperty('fields');
      expect(pane.fields).toBeInstanceOf(Array);
      expect(
        new Set(
          tabCmp
            .find(pane.pane.type)
            .findWhere(e => [FinalField, FieldArray].includes(e.type()))
            .map(x => x.prop('name'))
        )
      ).toEqual(new Set(pane.fields));
    }
  });
});
