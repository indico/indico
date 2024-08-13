// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import { Param, Plural, PluralTranslate, Singular } from 'indico/react/i18n';
import React, { HTMLAttributes, useState } from 'react'
import {
  AccordionTitle,
  AccordionContent,
  Accordion,
  Icon,
  TableRow,
  TableHeaderCell,
  TableHeader,
  TableCell,
  TableBody,
  Table,
  TableFooter,
  Popup,
  Segment,
} from 'semantic-ui-react'


import './ParticipantListAccordion.module.scss';
import { Translate } from 'react-jsx-i18n';

interface ParticipantListAccordionProps {
    tables: any
}

interface AccordionItemProps {
    index: number;
    table: any;
}

interface ParticipantCounterProps extends HTMLAttributes<HTMLSpanElement> {
    totalCount: number;
    hiddenCount: number;
    styleName?: string;
}

const ParticipantCountTranslationHidden: React.FC<{ count: number }> = ({ count }) => {
    return (
        <PluralTranslate count={count}>
            <Singular>
                <Param
                    name="anonymous-participants-count"
                    value={count}
                />{' '}
                participant registered anonymously.
            </Singular>
            <Plural>
                <Param
                    name="anonymous-participants-count"
                    value={count}
                />{' '}
                participants registered anonymously.
            </Plural>
        </PluralTranslate>
    )
}

const ParticipantCounter: React.FC<ParticipantCounterProps> = ({ styleName, totalCount, hiddenCount, ...props }) => {
    return (
        <div className={styleName} {...props}>
            <Popup
                position="left center"
                content={ <ParticipantCountTranslationHidden count={hiddenCount} /> }
                trigger={
                    <span>
                        { totalCount } <Icon name="user" />
                    </span>
                }
            />
        </div>
    );
};

function AccordionItem({ index, table }: AccordionItemProps) {
    const visibleParticipantsCount = table.rows.length
    const totalParticipantCount = table.num_participants;
    const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;
    const hasInvisibleParticipants = hiddenParticipantsCount > 0

    const [isActive, setIsActive] = useState(visibleParticipantsCount > 0);
    const handleClick = () => {
        setIsActive(!isActive);
    };

    const anonymousRegistrationText = (
        <PluralTranslate count={hiddenParticipantsCount}>
            <Singular>
                <Param
                    name="hidden-participants"
                    value={hiddenParticipantsCount}
                    />{' '}
                participant registered anonymously.
            </Singular>
            <Plural>
                <Param
                    name="hidden-participants"
                    value={hiddenParticipantsCount}
                    />{' '}
                participants registered anonymously.
            </Plural>
        </PluralTranslate>
    )

  
    return (
      <>
        <AccordionTitle
            active={isActive}
            onClick={handleClick}
            styleName="title"
        >
            <Icon name="dropdown" />
            {table.title}
            <ParticipantCounter
                styleName="participants-count-wrapper"
                totalCount={totalParticipantCount}
                hiddenCount={hiddenParticipantsCount}
            />
        </AccordionTitle>
        <AccordionContent active={isActive} key={`c${index}`}>
            { visibleParticipantsCount > 0 ?
                (
                    <Table celled>
                        <TableHeader>
                        <TableRow>
                            {table.headers.map((headerText: string, j: number) => (
                            <TableHeaderCell key={j}>
                                {headerText}
                            </TableHeaderCell>
                            ))}
                        </TableRow>
                        </TableHeader>
            
                        <TableBody>
                        {table.rows.map((row: any, j: number) => (
                            <TableRow key={j}>
                            {row.columns.map((col: any, k: number) => (
                                <TableCell key={`${j}-${k}`}>
                                {col.text}
                                </TableCell>
                            ))}
                            </TableRow>
                        ))}
                        </TableBody>
                        
                        { hasInvisibleParticipants &&
                            <TableFooter>
                                <TableRow>
                                    <TableHeaderCell colSpan="3">
                                        { anonymousRegistrationText }
                                    </TableHeaderCell>
                                </TableRow>
                            </TableFooter>
                        }
                    </Table>
                ) :
                (
                    <Segment>
                        { hasInvisibleParticipants ? anonymousRegistrationText : <Translate>No registrations</Translate> }
                    </Segment>
                )
            }
            </AccordionContent>
      </>
    );
  }

export default function ParticipantListAccordion({ tables }: ParticipantListAccordionProps) {
return (
    <Accordion styled fluid>
    {tables.map((table: any, i: number) => (
        <AccordionItem key={i} index={i} table={table} />
    ))}
    </Accordion>
);
}
