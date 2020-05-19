import attributesURL from 'indico-url:rb.admin_attributes';

import React from 'react';
import {mount} from 'enzyme';
import {Tab} from 'semantic-ui-react';
import {Provider} from 'react-redux';
import configureMockStore from 'redux-mock-store';
import {FieldArray} from 'react-final-form-arrays';
import {FinalField} from 'indico/react/forms';
import {useIndicoAxios, useFavoriteUsers} from 'indico/react/hooks';
import {usePermissionInfo} from 'indico/react/components/principals/hooks';
import RoomEditModal from '../edit/RoomEditModal';

jest.mock('indico/react/components/principals/hooks');
jest.mock('indico/react/components/principals/ACLField', () => () => null);
jest.mock('indico/react/hooks');

describe('RoomEditModal', () => {
  const mockStore = configureMockStore();

  useIndicoAxios.mockImplementation(({url}) => {
    if (url === attributesURL()) {
      return {data: [{name: 'foo', value: 'bar'}]};
    }
    return undefined;
  });

  usePermissionInfo.mockImplementation(() => {
    const permissionManager = {
      setPermissionForId: jest.fn(),
    };

    const permissionInfo = {
      permissions: {},
      tree: {},
      default: '',
    };

    return [permissionManager, permissionInfo];
  });

  useFavoriteUsers.mockImplementation(() => {
    return [{}, [null, null]];
  });

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
