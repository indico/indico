// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Accordion, Header} from 'semantic-ui-react';

import './CollapsibleContainer.module.scss';

export default function CollapsibleContainer({
  title,
  titleSize,
  defaultOpen,
  styled,
  dividing,
  children,
  ...rest
}) {
  return (
    <Accordion
      styleName="container"
      defaultActiveIndex={defaultOpen ? 0 : undefined}
      panels={[
        {
          key: 'container',
          title: styled
            ? title
            : {
                content: (
                  <Header styleName="header" size={titleSize} content={title} dividing={dividing} />
                ),
              },
          content: {
            content: children,
          },
        },
      ]}
      styled={styled}
      fluid
      {...rest}
    />
  );
}

CollapsibleContainer.propTypes = {
  title: PropTypes.string.isRequired,
  titleSize: PropTypes.string,
  defaultOpen: PropTypes.bool,
  styled: PropTypes.bool,
  dividing: PropTypes.bool,
  children: PropTypes.node.isRequired,
};

CollapsibleContainer.defaultProps = {
  titleSize: 'medium',
  defaultOpen: false,
  styled: false,
  dividing: false,
};
