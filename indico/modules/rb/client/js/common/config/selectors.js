// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {RequestState} from 'indico/utils/redux';

export const hasLoadedConfig = ({config}) => config.request.state === RequestState.SUCCESS;
export const getRoomsSpriteToken = ({config}) => config.data.roomsSpriteToken;
export const getTileServerURL = ({config}) => config.data.tileServerURL;
export const canManagersEditRooms = ({config}) => config.data.managersEditRooms;
export const getLanguages = ({config}) => config.data.languages;
export const getBookingGracePeriod = ({config}) => config.data.gracePeriod;
export const getHelpURL = ({config}) => config.data.helpURL;
export const hasTOS = ({config}) => config.data.hasTOS;
export const getTOSHTML = ({config}) => config.data.tosHTML;
export const hasPrivacyPolicy = ({config}) => config.data.hasPrivacyPolicy;
export const getPrivacyPolicyHTML = ({config}) => config.data.privacyPolicyHTML;
export const getContactEmail = ({config}) => config.data.contactEmail;
