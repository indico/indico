// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {UploadState} from '../files/util';

export const PictureState = {
  ...UploadState, // initial, uploading, error, finished
  capturing: 'capturing', // the camera is active and picture may be captured
  editing: 'editing', // picture is being edited
  dropzone: 'dropzone', // The picture was taken using the dropzone or upload dialog
};
