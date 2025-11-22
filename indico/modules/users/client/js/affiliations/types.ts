// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

interface AffiliationBase {
  name: string;
  altNames: string[];
  street: string;
  postcode: string;
  city: string;
  countryCode: string;
  [key: string]: unknown;
}

export interface Affiliation extends AffiliationBase {
  id: number;
  meta: Record<string, unknown>;
}

export type AffiliationFormValues = AffiliationBase;
