import {HTMLAttributes} from 'react';

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

export interface ParticipantAccordionProps {
  totalParticipantCount: number;
  published: boolean;
  tables: TableObj[];
}

export interface ParticipantAccordionItemProps {
  table: TableObj;
  collapsible?: boolean;
}

export interface ParticipantCounterProps extends HTMLAttributes<HTMLSpanElement> {
  totalCount: number;
  hiddenCount: number;
  styleName?: string;
}
