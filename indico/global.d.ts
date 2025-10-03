// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

declare const Indico: {
  User: {
    address: string;
    affiliation: string;
    affiliationId: number | null;
    affiliationMeta: object | null;
    avatarURL: string;
    email: string;
    favoriteUsers: Record<number, User>;
    firstName: string;
    fullName: string;
    id: number;
    identifier: string;
    isAdmin: boolean;
    language: string;
    lastName: string;
    mastodonServerName: string;
    mastodonServerURL: string;
    phone: string;
    title: string;
    type: string;
  };
};
