// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

export default function ProtectionStatus({category}) {
  return (
    <span className="protection-indicator" data-protected={category.is_protected}>
      {category.is_protected && <Translate as="span">Protected category</Translate>}
    </span>
  );
}

ProtectionStatus.propTypes = {
  category: PropTypes.shape({
    is_protected: PropTypes.bool,
  }).isRequired,
};
