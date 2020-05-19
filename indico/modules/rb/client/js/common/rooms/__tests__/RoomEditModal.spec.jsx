import attributesURL from 'indico-url:rb.admin_attributes';
import permissionInfoURL from 'indico-url:rb.permission_types';

import React from 'react';
import {act} from 'react-dom/test-utils';
import {mount} from 'enzyme';
import {Tab} from 'semantic-ui-react';
import {Provider} from 'react-redux';
import configureMockStore from 'redux-mock-store';
import {FieldArray} from 'react-final-form-arrays';
import axiosMock from 'jest-mock-axios';
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
        tabCmp
          .find(pane.pane.type)
          .findWhere(e => [FinalField, FieldArray].includes(e.type()))
          .map(x => x.prop('name'))
          .filter((v, i, a) => a.indexOf(v) === i)
          .sort()
      ).toEqual(pane.fields.sort());
    }
  });
});
