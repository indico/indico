// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

interface AffiliationBase {
  name: string;
  alt_names: string[];
  street: string;
  postcode: string;
  city: string;
  country_code: string;
  meta: Record<string, unknown>;
  [key: string]: unknown;
}

export interface Affiliation extends AffiliationBase {
  id: number;
  country_name: string;
}

export type AffiliationFormValues = AffiliationBase;
