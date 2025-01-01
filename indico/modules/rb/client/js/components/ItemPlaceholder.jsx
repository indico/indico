// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Item, Placeholder} from 'semantic-ui-react';

export default function ItemPlaceholder() {
  return (
    <Item>
      <Item.Image>
        <Placeholder>
          <Placeholder.Image />
        </Placeholder>
      </Item.Image>
      <Item.Content>
        <Placeholder>
          <Placeholder.Line length="very short" />
        </Placeholder>
        <Item.Meta>
          <Placeholder>
            <Placeholder.Line length="short" />
          </Placeholder>
        </Item.Meta>
        <Item.Description>
          <Placeholder>
            <Placeholder.Line length="full" />
            <Placeholder.Line length="full" />
          </Placeholder>
        </Item.Description>
      </Item.Content>
    </Item>
  );
}

function ItemPlaceholderGroup({count}) {
  return (
    <Item.Group>
      {_.range(0, count).map(i => (
        <ItemPlaceholder key={i} />
      ))}
    </Item.Group>
  );
}

ItemPlaceholderGroup.propTypes = {
  count: PropTypes.number.isRequired,
};

ItemPlaceholder.Group = ItemPlaceholderGroup;
