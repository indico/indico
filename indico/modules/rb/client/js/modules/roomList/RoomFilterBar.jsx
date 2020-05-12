// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Button, Icon, Label} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Overridable from 'react-overridable';

import {Translate, Param} from 'indico/react/i18n';
import {Responsive} from 'indico/react/util';

import CapacityForm from './filters/CapacityForm';
import EquipmentForm from './filters/EquipmentForm';
import BuildingForm from './filters/BuildingForm';
import ShowOnlyForm from './filters/ShowOnlyForm';
import {FilterBarController, FilterDropdownFactory} from '../../common/filters/FilterBar';
import {actions as filtersActions} from '../../common/filters';
import {selectors as userSelectors} from '../../common/user';

import {selectors as roomsSelectors} from '../../common/rooms';
import './RoomFilterBar.module.scss';

/* eslint-disable react/prop-types */
const renderCapacity = ({capacity}) =>
  capacity === null ? null : (
    <span>
      <Icon name="user" />
      {capacity}
    </span>
  );

const renderEquipment = ({equipment, features}) => {
  const count = equipment.length + features.length;
  if (!count) {
    return null;
  }
  return (
    <>
      <Responsive.Tablet andLarger orElse={<Icon name="wrench" />}>
        <Translate>Equipment</Translate>
      </Responsive.Tablet>
      <Label circular horizontal className="white" size="tiny" styleName="filter-bar-button-label">
        {count}
      </Label>
    </>
  );
};

const renderBuilding = ({building}) => {
  if (!building) {
    return null;
  }

  return (
    <>
      <Icon name="building" />
      <Responsive.Tablet andLarger orElse={building}>
        <Translate>
          Building <Param name="building" value={building} />
        </Translate>
      </Responsive.Tablet>
    </>
  );
};
/* eslint-enable react/prop-types */

export class RoomFilterBarBase extends React.Component {
  static propTypes = {
    equipmentTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
    features: PropTypes.arrayOf(
      PropTypes.shape({
        icon: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        title: PropTypes.string.isRequired,
      })
    ).isRequired,
    buildings: PropTypes.array.isRequired,
    showOnlyAuthorizedFilter: PropTypes.bool,
    extraButtons: PropTypes.node,
    hasOwnedRooms: PropTypes.bool.isRequired,
    filters: PropTypes.shape({
      building: PropTypes.string,
      capacity: PropTypes.number,
      equipment: PropTypes.array,
      onlyFavorites: PropTypes.bool,
      onlyMine: PropTypes.bool,
      onlyAuthorized: PropTypes.bool,
      features: PropTypes.arrayOf(PropTypes.string).isRequired,
    }).isRequired,
    actions: PropTypes.shape({
      setFilterParameter: PropTypes.func,
      setFilters: PropTypes.func,
    }).isRequired,
    hideOptions: PropTypes.objectOf(PropTypes.bool),
    disabled: PropTypes.bool,
  };

  static defaultProps = {
    showOnlyAuthorizedFilter: true,
    extraButtons: null,
    hideOptions: {},
    disabled: false,
  };

  render() {
    const {
      equipmentTypes,
      features: availableFeatures,
      buildings,
      extraButtons,
      hideOptions,
      disabled,
      showOnlyAuthorizedFilter,
      hasOwnedRooms,
      filters: {
        capacity,
        onlyFavorites,
        onlyMine,
        onlyAuthorized,
        equipment,
        features,
        building,
        ...extraFilters
      },
      actions: {setFilterParameter, setFilters},
    } = this.props;
    const hideShowOnlyForm =
      hideOptions.favorites && !hasOwnedRooms && !onlyMine && !showOnlyAuthorizedFilter;
    const responsiveTitle = (title, orElse) => (
      <Responsive.Desktop andLarger orElse={orElse}>
        {title}
      </Responsive.Desktop>
    );
    const equipmentFilter = (!!equipmentTypes.length || !!availableFeatures.length) && (
      <FilterDropdownFactory
        name="equipment"
        title={responsiveTitle(Translate.string('Equipment'), <Icon name="wrench" />)}
        form={(values, setParentField) => (
          <EquipmentForm
            setParentField={setParentField}
            selectedEquipment={values.equipment}
            selectedFeatures={values.features}
            availableEquipment={equipmentTypes}
            availableFeatures={availableFeatures}
          />
        )}
        counter
        setGlobalState={setFilters}
        initialValues={{equipment, features}}
        renderValue={renderEquipment}
        disabled={disabled}
      />
    );

    return (
      <Button.Group size="small">
        <Button icon="filter" as="div" disabled />
        <FilterBarController>
          {!hideOptions.building && (
            <FilterDropdownFactory
              name="building"
              title={responsiveTitle(Translate.string('Building'), <Icon name="building" />)}
              form={({building: selectedBuilding}, setParentField) => (
                <BuildingForm
                  setParentField={setParentField}
                  buildings={buildings}
                  building={selectedBuilding}
                />
              )}
              setGlobalState={data => setFilterParameter('building', data.building)}
              initialValues={{building}}
              renderValue={renderBuilding}
              disabled={disabled}
            />
          )}
          {!hideOptions.capacity && (
            <FilterDropdownFactory
              name="capacity"
              title={responsiveTitle(Translate.string('Min. Capacity'), <Icon name="user" />)}
              form={({capacity: selectedCapacity}, setParentField) => (
                <CapacityForm setParentField={setParentField} capacity={selectedCapacity} />
              )}
              setGlobalState={data => setFilterParameter('capacity', data.capacity)}
              initialValues={{capacity}}
              renderValue={renderCapacity}
              disabled={disabled}
            />
          )}
          {!hideOptions.equipment && equipmentFilter}
          <Overridable
            id="RoomFilterBar.extraFilters"
            setFilter={setFilterParameter}
            filters={extraFilters}
            disabled={disabled}
          />
          {!hideShowOnlyForm && (
            <FilterDropdownFactory
              name="room-different"
              title={responsiveTitle(Translate.string('Show only...'), '...')}
              form={(data, setParentField) => (
                <ShowOnlyForm
                  {...data}
                  setParentField={setParentField}
                  showOnlyAuthorizedFilter={showOnlyAuthorizedFilter}
                  hideFavoritesFilter={hideOptions.favorites}
                  disabled={disabled}
                />
              )}
              setGlobalState={setFilters}
              renderValue={data => {
                const iconMap = {
                  onlyFavorites: 'star',
                  onlyMine: 'user',
                  onlyAuthorized: 'lock open',
                };
                const icons = Object.entries(iconMap)
                  .filter(([key]) => data[key])
                  .map(([key, icon]) => <Icon key={key} name={icon} />);
                return icons.length !== 0 ? icons : null;
              }}
              initialValues={{onlyFavorites, onlyMine, onlyAuthorized}}
              disabled={disabled}
            />
          )}
          {extraButtons}
        </FilterBarController>
      </Button.Group>
    );
  }
}

export default (namespace, searchRoomsSelectors) =>
  connect(
    state => ({
      filters: searchRoomsSelectors.getFilters(state),
      equipmentTypes: roomsSelectors.getUsedEquipmentTypeNamesWithoutFeatures(state),
      features: roomsSelectors.getFeatures(state),
      buildings: roomsSelectors.getBuildings(state),
      hasOwnedRooms: userSelectors.hasOwnedRooms(state),
    }),
    dispatch => ({
      actions: bindActionCreators(
        {
          setFilterParameter: (param, value) =>
            filtersActions.setFilterParameter(namespace, param, value),
          setFilters: params => filtersActions.setFilters(namespace, params),
        },
        dispatch
      ),
    })
  )(Overridable.component('RoomFilterBar', RoomFilterBarBase));
