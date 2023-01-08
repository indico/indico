// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const SET_FORM_DATA = 'Set form data';

export function setFormData(data) {
  return {type: SET_FORM_DATA, items: data.items, sections: data.sections};
}
