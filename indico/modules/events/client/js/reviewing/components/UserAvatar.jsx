// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

function UserAvatar({user}) {
  return (
    <div
      className="i-timeline-item-label avatar-placeholder"
      style={{backgroundColor: user.avatarBgColor}}
    >
      {user.anonymous ? '' : user.fullName[0]}
    </div>
  );
}

UserAvatar.propTypes = {
  user: PropTypes.shape({
    anonymous: PropTypes.bool,
    fullName: PropTypes.string.isRequired,
    avatarBgColor: PropTypes.string.isRequired,
  }).isRequired,
};

export default React.memo(UserAvatar);
