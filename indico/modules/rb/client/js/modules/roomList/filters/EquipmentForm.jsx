// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Accordion, Form, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {FilterFormComponent} from '../../../common/filters';

import './EquipmentForm.module.scss';

export default class EquipmentForm extends FilterFormComponent {
  static propTypes = {
    selectedEquipment: PropTypes.arrayOf(PropTypes.string).isRequired,
    selectedFeatures: PropTypes.arrayOf(PropTypes.string).isRequired,
    availableEquipment: PropTypes.arrayOf(PropTypes.string).isRequired,
    availableFeatures: PropTypes.arrayOf(
      PropTypes.shape({
        name: PropTypes.string.isRequired,
        title: PropTypes.string.isRequired,
      })
    ).isRequired,
    ...FilterFormComponent.propTypes,
  };

  constructor(props) {
    super(props);
    const {availableEquipment, availableFeatures, selectedEquipment, selectedFeatures} = props;
    this.state = {
      equipment: availableEquipment.filter(eq => selectedEquipment.includes(eq)),
      features: availableFeatures.map(f => f.name).filter(f => selectedFeatures.includes(f)),
      showEquipment: !!selectedEquipment.length,
    };
  }

  setEquipment(eqName, value) {
    const {setParentField} = this.props;

    this.setState(
      oldState => {
        const equipmentList = _.without(oldState.equipment, eqName);
        if (value) {
          equipmentList.push(eqName);
        }
        return {
          equipment: equipmentList,
        };
      },
      () => {
        setParentField('equipment', this.state.equipment);
      }
    );
  }

  setFeature(featName, value) {
    const {setParentField} = this.props;

    this.setState(
      oldState => {
        const featureList = _.without(oldState.features, featName);
        if (value) {
          featureList.push(featName);
        }
        return {features: featureList};
      },
      () => {
        setParentField('features', this.state.features);
      }
    );
  }

  handleClick = () => {
    const {showEquipment} = this.state;
    this.setState({showEquipment: !showEquipment});
  };

  render() {
    const {availableEquipment, availableFeatures} = this.props;
    const {equipment, features, showEquipment} = this.state;
    return (
      <Form.Group>
        {availableFeatures.map(feat => (
          <Form.Checkbox
            checked={features.includes(feat.name)}
            key={feat.name}
            label={
              <label>
                <Icon name={feat.icon} />
                <strong>{feat.title}</strong>
              </label>
            }
            onChange={(__, {checked}) => {
              this.setFeature(feat.name, checked);
            }}
          />
        ))}
        {!!availableFeatures.length && !!availableEquipment.length && (
          <Accordion styleName="equipment-accordion">
            <Accordion.Title active={showEquipment} index={0} onClick={this.handleClick}>
              <Icon name="dropdown" />
              <Translate>See detailed equipment</Translate>
            </Accordion.Title>
            <Accordion.Content active={showEquipment}>
              {availableEquipment.map(equip => (
                <Form.Checkbox
                  checked={equipment.includes(equip)}
                  key={equip}
                  label={equip}
                  onChange={(__, {checked}) => {
                    this.setEquipment(equip, checked);
                  }}
                />
              ))}
            </Accordion.Content>
          </Accordion>
        )}
        {!availableFeatures.length &&
          availableEquipment.map(equip => (
            <Form.Checkbox
              checked={equipment.includes(equip)}
              key={equip}
              label={equip}
              onChange={(__, {checked}) => {
                this.setEquipment(equip, checked);
              }}
            />
          ))}
      </Form.Group>
    );
  }
}
