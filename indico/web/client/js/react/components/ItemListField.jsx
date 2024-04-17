// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Button, Ref} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

import './ItemListField.module.scss';

const itemValueShapeSchema = PropTypes.shape({
  name: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  as: PropTypes.elementType,
  fieldProps: PropTypes.oneOfType([PropTypes.object, PropTypes.func]),
  defaultValue: PropTypes.any,
  width: PropTypes.string,
});

function Item({
  value,
  shape,
  index,
  id,
  canRemove,
  isEnabledKey,
  onChange,
  onMove,
  onFocus,
  onBlur,
  onDelete,
  disabled,
  sortable,
  children,
  ...rest
}) {
  const makeOnChange = field => evt => {
    const elem = evt.target;
    if (elem.type === 'checkbox') {
      onChange(field, elem.checked);
    } else if (elem.type === 'number') {
      onChange(field, +elem.value);
    } else {
      onChange(field, elem.value);
    }
  };

  return (
    <tr styleName={isEnabledKey && !value[isEnabledKey] ? 'disabled-row' : undefined} {...rest}>
      {children}
      {shape.map(({name, as, defaultValue, fieldProps}) => {
        const Component = as || 'input';
        const newDefault = defaultValue === undefined ? '' : defaultValue;
        const extraProps =
          typeof fieldProps === 'function' ? fieldProps(value, onChange) : fieldProps || {};
        return (
          <td key={name}>
            <Component
              name={name}
              value={value[name] || newDefault}
              onChange={makeOnChange(name)}
              onFocus={onFocus}
              onBlur={onBlur}
              {...extraProps}
            />
          </td>
        );
      })}
      <td style={{textAlign: 'end'}}>
        {canRemove && (
          <a
            className="icon-remove remove-row"
            title={Translate.string('Remove row')}
            onClick={disabled ? undefined : onDelete}
          />
        )}
        {isEnabledKey &&
          (value[isEnabledKey] ? (
            <a
              className="icon-disable"
              title={Translate.string('Disable choice')}
              onClick={() => onChange(isEnabledKey, false)}
            />
          ) : (
            <a
              className="icon-checkmark remove-row"
              title={Translate.string('Enable choice')}
              onClick={() => onChange(isEnabledKey, true)}
            />
          ))}
      </td>
    </tr>
  );
}

Item.propTypes = {
  index: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onMove: PropTypes.func.isRequired,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
  onDelete: PropTypes.func.isRequired,
  shape: PropTypes.arrayOf(itemValueShapeSchema).isRequired,
  value: PropTypes.object.isRequired,
  disabled: PropTypes.bool.isRequired,
  sortable: PropTypes.bool.isRequired,
  canRemove: PropTypes.bool,
  isEnabledKey: PropTypes.string,
  children: PropTypes.node,
};

Item.defaultProps = {
  onFocus: null,
  onBlur: null,
  canRemove: true,
  isEnabledKey: null,
  children: null,
};

function DraggableItem(props) {
  const {index, id, onMove, disabled} = props;
  const [handleRef, itemRef, style] = useSortableItem({
    type: 'item-list-field-item',
    id,
    index,
    active: !disabled,
    separateHandle: true,
    moveItem: onMove,
    // nothing to do since we don't need to "save" at the end
    onDrop: () => null,
  });

  return (
    <Ref innerRef={itemRef}>
      <Item {...props} style={style}>
        <td styleName="table-sortable-handle" ref={handleRef} />
      </Item>
    </Ref>
  );
}

DraggableItem.propTypes = {
  ...Item.propTypes,
};

export default function ItemListField({
  value,
  onChange,
  itemShape,
  sortable,
  disabled,
  canDisableItem,
  canRemoveItem,
  isItemEnabledKey,
  idKey,
  generateNewItemId,
  ...rest
}) {
  const makeOnDelete = index => () => onChange(value.filter((__, idx) => index !== idx));
  const makeOnChange = index => (field, val) =>
    onChange(value.map((choice, idx) => (index !== idx ? choice : {...choice, [field]: val})));
  const handleMove = (sourceIndex, targetIndex) => {
    const newValue = [...value];
    const sourceItem = newValue[sourceIndex];
    newValue.splice(sourceIndex, 1);
    newValue.splice(targetIndex, 0, sourceItem);
    onChange(newValue);
  };
  const handleAdd = () => {
    const newItem = Object.fromEntries(
      itemShape.map(item => [item.name, item.defaultValue === undefined ? '' : item.defaultValue])
    );
    if (canDisableItem && !(isItemEnabledKey in newItem)) {
      newItem[isItemEnabledKey] = true;
    }
    if (!(idKey in newItem)) {
      newItem[idKey] = generateNewItemId ? generateNewItemId() : nanoid();
    }
    onChange([...value, newItem]);
  };

  const ItemComponent = sortable ? DraggableItem : Item;

  // TODO: style this nicely, ideally ditch the table and find a better way to do this
  // one option could be showing just the text and settings (icons?), and using a more
  // explicit edit action on the individual entries (which could then use a modal to
  // edit  the actual data)
  const itemsTable = (
    <table styleName="items-table">
      <thead>
        <tr>
          {sortable && <th style={{width: '1.75em'}} />}
          {itemShape.map(({name, title, width}) => (
            <th key={name} style={{width}}>
              {title}
            </th>
          ))}
          <th style={{width: '3.7em'}} />
        </tr>
      </thead>
      <tbody>
        {value.map((item, idx) => (
          <ItemComponent
            key={item[idKey]}
            index={idx}
            id={item[idKey]}
            onChange={makeOnChange(idx)}
            onDelete={makeOnDelete(idx)}
            onMove={handleMove}
            shape={itemShape}
            value={item}
            sortable={sortable}
            disabled={disabled}
            isEnabledKey={canDisableItem ? isItemEnabledKey : null}
            canRemove={canRemoveItem(item)}
            {...rest}
          />
        ))}
      </tbody>
    </table>
  );
  return (
    <>
      {sortable ? (
        <SortableWrapper styleName="items-table-wrapper" accept="item-list-field-item">
          {itemsTable}
        </SortableWrapper>
      ) : (
        <div styleName="items-table-wrapper">{itemsTable}</div>
      )}
      <Button type="button" onClick={handleAdd} disabled={disabled}>
        <Translate>Add new</Translate>
      </Button>
    </>
  );
}

ItemListField.propTypes = {
  onChange: PropTypes.func.isRequired,
  value: PropTypes.array.isRequired,
  itemShape: PropTypes.arrayOf(itemValueShapeSchema).isRequired,
  disabled: PropTypes.bool,
  sortable: PropTypes.bool,
  canDisableItem: PropTypes.bool,
  canRemoveItem: PropTypes.func,
  isItemEnabledKey: PropTypes.string,
  idKey: PropTypes.string,
  generateNewItemId: PropTypes.func,
};

ItemListField.defaultProps = {
  disabled: false,
  sortable: false,
  canDisableItem: false,
  canRemoveItem: () => true,
  isItemEnabledKey: 'enabled',
  idKey: 'id',
  generateNewItemId: null,
};

export function FinalItemListField(props) {
  const {sortable} = props;
  const finalField = <FinalField component={ItemListField} isEqual={_.isEqual} {...props} />;
  return sortable ? <DndProvider backend={HTML5Backend}>{finalField}</DndProvider> : finalField;
}

FinalItemListField.propTypes = {
  name: PropTypes.string.isRequired,
  sortable: PropTypes.bool,
};

FinalItemListField.defaultProps = {
  sortable: false,
};
