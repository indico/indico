// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export enum PreviewEnum {
  GUEST = 'guest',
  PARTICIPANT = 'participant',
}

export interface TableColumnObj {
  id: number;
  text: string;
  is_picture: boolean;
}

export interface TableRowObj {
  id: number;
  checked_in: boolean;
  columns: TableColumnObj[];
}

export interface TableObj {
  headers: string[];
  rows: TableRowObj[];
  num_participants: number;
  show_checkin: boolean;
  title?: string;
}
