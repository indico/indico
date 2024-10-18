// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import referenceTypesURL from 'indico-url:events.api_reference_types';

import _ from 'lodash';
import {nanoid} from 'nanoid';
import React from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Button, Form, Ref} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

import './ItemListField.module.scss';

interface ItemShapeType {
  name: string;
  title: string;
  as?: React.ElementType;
  render?: (value: any) => boolean;
  fieldProps?: object | ((value: any, onChange: (field: string, value: any) => void) => object);
  defaultValue?: any;
  width?: string;
}

interface ItemProps {
  value: any;
  shape: ItemShapeType[];
  onChange: (field: string, value: any) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onDelete: () => void;
  disabled: boolean;
  canRemove?: boolean;
  canDisableItem?: boolean;
  children?: React.ReactNode;
}

function Item({
  value,
  shape,
  canRemove = true,
  canDisableItem = false,
  onChange,
  onFocus,
  onBlur,
  onDelete,
  disabled,
  children,
  ...rest
}: ItemProps) {
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
    <tr styleName={canDisableItem && !value.isEnabled ? 'disabled-row' : undefined} {...rest}>
      {children}
      {shape.map(({name, as, render, defaultValue, fieldProps}) => {
        if (render && !render(value)) {
          return <td key={name} />;
        }
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
              type={as ? undefined : 'text'}
              {...extraProps}
            />
          </td>
        );
      })}
      <td>
        {canRemove && (
          <a
            className="icon-remove remove-row"
            title={Translate.string('Remove row')}
            onClick={disabled ? undefined : onDelete}
          />
        )}
        {canDisableItem &&
          (value.isEnabled ? (
            <a
              className="icon-disable"
              title={Translate.string('Disable choice')}
              onClick={() => onChange('isEnabled', false)}
            />
          ) : (
            <a
              className="icon-checkmark remove-row"
              title={Translate.string('Enable choice')}
              onClick={() => onChange('isEnabled', true)}
            />
          ))}
      </td>
    </tr>
  );
}

interface DraggableItemProps extends ItemProps {
  index: number;
  id: string;
  onMove: (sourceIndex: number, targetIndex: number) => void;
}

function DraggableItem(props: DraggableItemProps) {
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

interface ItemListFieldProps {
  itemShape: ItemShapeType[];
  sortable?: boolean;
  disabled?: boolean;
  scrollable?: boolean;
  canDisableItem?: boolean;
  canRemoveItem?: (item: object) => boolean;
}

interface ItemListFieldComponentProps extends ItemListFieldProps {
  value: object[];
  onChange: (value: object[]) => void;
}

export default function ItemListField({
  value,
  onChange,
  itemShape,
  sortable = false,
  disabled = false,
  scrollable = false,
  canDisableItem = false,
  canRemoveItem = () => true,
  ...rest
}: ItemListFieldComponentProps) {
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
    if (canDisableItem && !('isEnabled' in newItem)) {
      newItem.isEnabled = true;
    }
    if (!('id' in newItem)) {
      newItem.id = `new:${nanoid()}`;
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
          <th />
        </tr>
      </thead>
      <tbody>
        {value.map((item, idx) => (
          <ItemComponent
            key={item.id}
            index={idx}
            id={item.id}
            onChange={makeOnChange(idx)}
            onDelete={makeOnDelete(idx)}
            onMove={handleMove}
            shape={itemShape}
            value={item}
            disabled={disabled}
            canDisableItem={canDisableItem}
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
        <SortableWrapper
          styleName={scrollable ? 'items-table-wrapper' : undefined}
          accept="item-list-field-item"
        >
          {itemsTable}
        </SortableWrapper>
      ) : (
        <div styleName={scrollable ? 'items-table-wrapper' : undefined}>{itemsTable}</div>
      )}
      <Button type="button" onClick={handleAdd} disabled={disabled}>
        <Translate>Add new</Translate>
      </Button>
    </>
  );
}

interface FinalItemListProps extends ItemListFieldProps {
  name: string;
  required?: boolean;
  description?: string;
}

export function FinalItemList(props: FinalItemListProps) {
  const {sortable = false} = props;
  const finalField = <FinalField component={ItemListField} isEqual={_.isEqual} {...props} />;
  return sortable ? <DndProvider backend={HTML5Backend}>{finalField}</DndProvider> : finalField;
}

export function FinalReferences({name, ...rest}: FinalItemListProps) {
  const {data, loading} = useIndicoAxios(referenceTypesURL(), {camelize: true});
  const referenceTypes = data || [];

  return (
    <FinalItemList
      name={name}
      itemShape={[
        {
          name: 'type',
          title: Translate.string('Type'),
          as: Form.Select,
          fieldProps: (item, onChange) => ({
            options: referenceTypes.map(r => ({key: r.id, value: r.id, text: r.name})),
            onChange: (__, {value}) => onChange('type', value),
            loading,
            required: true,
          }),
        },
        {name: 'value', title: Translate.string('Value'), fieldProps: {required: true}},
      ]}
      {...rest}
    />
  );
}
