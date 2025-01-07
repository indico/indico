// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export function setNativeInputValue(input, value) {
  // React adds its own setter to the input and messes with the native event mechanism.
  // In order for the value to be set in a standard way, we need to resort to this hack.
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, value);
}
