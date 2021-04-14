// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default function TimelineContent({blocks, itemComponent: Component}) {
  return blocks.map((block, index) => {
    return (
      <React.Fragment key={block.id}>
        {index !== 0 && (
          <div className="i-timeline">
            <div className="i-timeline to-separator-wrapper">
              <div className="i-timeline-connect-down to-separator" />
            </div>
          </div>
        )}
        <Component block={block} index={index} />
      </React.Fragment>
    );
  });
}

TimelineContent.propTypes = {
  blocks: PropTypes.array.isRequired,
  itemComponent: PropTypes.elementType.isRequired,
};
