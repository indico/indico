import React from 'react';

interface ParticipantListAccordionProps {
    title: string;
}

export default function ParticipantListAccordion({ title }: ParticipantListAccordionProps) {
    return (
        <p>{title}</p>
    );
}
