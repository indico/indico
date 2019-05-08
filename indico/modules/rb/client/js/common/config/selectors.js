// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {RequestState} from 'indico/utils/redux';


export const hasLoadedConfig = ({config}) => config.request.state === RequestState.SUCCESS;
export const getRoomsSpriteToken = ({config}) => config.data.roomsSpriteToken;
export const getTileServerURL = ({config}) => config.data.tileServerURL;
export const getLanguages = ({config}) => config.data.languages;
export const getBookingGracePeriod = ({config}) => config.data.gracePeriod;
