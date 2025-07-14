// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const hasLinkObject = ({linking}) => linking.type !== null;
export const getLinkObject = ({linking}) => (linking.type !== null ? linking : null);
export const getLinkingDisplayRange = ({linking: {earlier, later}}) => ({earlier, later});
