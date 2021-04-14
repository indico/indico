// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

export const linkDataShape = PropTypes.shape({
  type: PropTypes.oneOf(['event', 'contribution', 'sessionBlock']).isRequired,
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  eventURL: PropTypes.string.isRequired,
  eventTitle: PropTypes.string.isRequired,
  ownRoomId: PropTypes.number,
  ownRoomName: PropTypes.string,
});
