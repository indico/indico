// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Table, Checkbox} from 'semantic-ui-react';

import './SideBar.module.scss';

export default function SideBar({query, aggregations, onChange}) {
  const handleChange = (type, value) =>
    onChange && onChange(query[type] === value ? undefined : value, type);

  return Object.entries(aggregations)
    .filter(([, {buckets}]) => buckets && buckets.length)
    .map(([key, {label, buckets}]) => (
      <AggregationList
        key={key}
        name={key}
        title={label}
        items={buckets}
        query={query}
        onChange={handleChange}
      />
    ));
}

function AggregationList({name, title, items, query, onChange}) {
  items = items
    .filter(b => b.key)
    .map(({key, filter, count}) => ({
      key: filter,
      label: key.charAt(0).toUpperCase() + key.slice(1),
      count,
    }));

  if (!items.length) {
    return null;
  }

  return (
    <Table fixed singleLine celled padded unstackable>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell styleName="capitalize">{title}</Table.HeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {items.map(({key, label, count}) => (
          <Table.Row key={key}>
            <Table.Cell>
              <Checkbox
                styleName="checkbox"
                label={`${label} (${count})`}
                checked={query[name] === key}
                onChange={() => onChange(name, key)}
              />
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

AggregationList.propTypes = {
  name: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  items: PropTypes.array.isRequired,
  query: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
};

SideBar.propTypes = {
  query: PropTypes.object,
  aggregations: PropTypes.object,
  onChange: PropTypes.func,
};

SideBar.defaultProps = {
  query: {},
  aggregations: {},
  onChange: undefined,
};
