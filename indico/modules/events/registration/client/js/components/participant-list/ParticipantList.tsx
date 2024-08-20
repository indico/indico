import React from 'react';

import ParticipantAccordion from './ParticipantAccordion';
import {ParticipantAccordionProps} from './types';

export default function ParticipantListAccordion({
  published,
  totalParticipantCount,
  tables,
}: ParticipantAccordionProps) {
  return (
    <ParticipantAccordion
      published={published}
      totalParticipantCount={totalParticipantCount}
      tables={tables}
    />
  );
}
