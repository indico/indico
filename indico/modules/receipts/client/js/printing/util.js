// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import imagesURL from 'indico-url:receipts.images';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

export const getDefaultFieldValue = f => {
  if (f.type === 'dropdown') {
    return f.attributes.options[f.attributes.default];
  } else if (f.type === 'checkbox') {
    return f.attributes.value || false;
  } else if (f.type === 'image') {
    return null;
  } else {
    return f.attributes.value || '';
  }
};

export const fetchEventImages = async (images, setImages, eventId) => {
  let response;
  try {
    response = await indicoAxios.get(imagesURL({event_id: eventId}));
  } catch (error) {
    return handleAxiosError(error);
  }
  const fetchedImages = response.data.images;
  console.debug('fetchEventImages', fetchedImages);
  const trimmedImages = images.filter(
    x => !!fetchedImages.find(y => x.identifier === y.identifier)
  );
  const newImages = fetchedImages.filter(x => !images.find(y => x.identifier === y.identifier));
  setImages([...trimmedImages, ...newImages].sort((a, b) => a.filename.localeCompare(b.filename)));
  console.debug(
    'setImages',
    [...trimmedImages, ...newImages].sort((a, b) => a.filename.localeCompare(b.filename))
  );
};
