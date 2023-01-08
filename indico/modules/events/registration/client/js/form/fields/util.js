// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export function mapPropsToAttributes(props, mapping, defaults) {
  const inputProps = {};
  Object.entries(mapping).forEach(([prop, attr]) => {
    const val = props[prop];
    if (val === null && prop in defaults) {
      inputProps[attr] = defaults[prop];
    } else if (val > 0) {
      inputProps[attr] = val;
    }
  });
  return inputProps;
}
