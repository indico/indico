// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Card, Placeholder} from 'semantic-ui-react';

export default function CardPlaceholder({withImage}) {
  return (
    <Card>
      {withImage && (
        <Placeholder>
          <Placeholder.Image />
        </Placeholder>
      )}
      <Card.Content>
        <Placeholder>
          <Placeholder.Header>
            <Placeholder.Line length="very short" />
            <Placeholder.Line length="medium" />
          </Placeholder.Header>
          <Placeholder.Paragraph>
            <Placeholder.Line length="short" />
          </Placeholder.Paragraph>
        </Placeholder>
      </Card.Content>
      <Card.Content extra>
        <Placeholder>
          <Placeholder.Line length="short" />
        </Placeholder>
      </Card.Content>
    </Card>
  );
}

CardPlaceholder.propTypes = {
  withImage: PropTypes.bool,
};

CardPlaceholder.defaultProps = {
  withImage: true,
};

function CardPlaceholderGroup({count, className, itemsPerRow, withImage}) {
  const props = className ? {className} : {};
  return (
    <Card.Group {...props} itemsPerRow={itemsPerRow} stackable>
      {_.range(0, count).map(i => (
        <CardPlaceholder key={i} withImage={withImage} />
      ))}
    </Card.Group>
  );
}

CardPlaceholderGroup.propTypes = {
  count: PropTypes.number.isRequired,
  className: PropTypes.string,
  itemsPerRow: PropTypes.number,
  withImage: PropTypes.bool,
};

CardPlaceholderGroup.defaultProps = {
  className: null,
  itemsPerRow: null,
  withImage: true,
};

CardPlaceholder.Group = CardPlaceholderGroup;
