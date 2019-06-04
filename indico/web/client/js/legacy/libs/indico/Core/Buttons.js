// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

IndicoUI.Buttons = {
  /**
   * Returns an image with an 'remove' icon
   */
  removeButton: function(faded, fadedCaption) {
    var caption = faded ? (exists(fadedCaption) ? fadedCaption : 'Remove (blocked)') : 'Remove';
    return Html.img({
      alt: caption,
      title: caption,
      src: faded ? imageSrc('remove_faded') : imageSrc('remove'),
      style: {
        marginLeft: '5px',
        verticalAlign: 'middle',
      },
    });
  },
  /**
   * Returns an image with an 'edit' icon
   */
  editButton: function(faded, fadedCaption) {
    var caption = faded ? (exists(fadedCaption) ? fadedCaption : 'Edit (blocked)') : 'Edit';
    return Html.img({
      alt: caption,
      title: caption,
      src: faded ? imageSrc('edit_faded') : imageSrc('edit'),
      style: {
        marginLeft: '5px',
        verticalAlign: 'middle',
      },
    });
  },
};
