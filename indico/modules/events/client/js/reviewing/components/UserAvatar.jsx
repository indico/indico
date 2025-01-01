// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import imageURL from 'indico-url:assets.image';

import PropTypes from 'prop-types';
import React from 'react';
import {Image} from 'semantic-ui-react';

function UserAvatar({user}) {
  return (
    <div>
      <Image
        avatar
        src={user.avatarURL || imageURL({filename: 'robot.svg'})}
        className="profile-picture"
      />
    </div>
  );
}

UserAvatar.propTypes = {
  user: PropTypes.shape({
    avatarURL: PropTypes.string,
  }).isRequired,
};

export default React.memo(UserAvatar);
