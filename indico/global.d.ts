// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Justification of this file found in issue below
// https://github.com/gajus/babel-plugin-react-css-modules/issues/292

declare namespace React {
  interface Attributes {
    styleName?: string;
  }
  interface HTMLAttributes<T> {
    styleName?: string;
  }
  interface SVGAttributes<T> {
    styleName?: string;
  }
}
