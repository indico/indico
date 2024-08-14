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
  Message,
} from 'semantic-ui-react'

import './ParticipantListAccordion.module.scss';


interface TableObj {
    headers: string[];
    rows: object[];
    num_participants: number;
    show_checkin: boolean;
    title?: string;
}

interface ParticipantListAccordionProps {
    tables: TableObj[];
}

interface AccordionParticipantsItemProps {
    index: number;
    table: TableObj;
    children?: any;
    startsOpen?: boolean;
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

const ParticipantCounter: React.FC<ParticipantCounterProps> = ({ styleName, totalCount, hiddenCount, ...props }) => (
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

function ParticipantTable({ table }: { table: TableObj }) {
    const visibleParticipantsCount = table.rows.length
    const totalParticipantCount = table.num_participants;
    const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;
    const hasInvisibleParticipants = hiddenParticipantsCount > 0

    return (
        visibleParticipantsCount > 0 ? (
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
                            <TableHeaderCell colSpan={ table.headers.length }>
                                <ParticipantCountTranslationHidden count={ hiddenParticipantsCount }/>
                            </TableHeaderCell>
                        </TableRow>
                    </TableFooter>
                }
            </Table>
        ) :
        (
            <Message>
                <ParticipantCountTranslationHidden count={ hiddenParticipantsCount }/>
            </Message>
        )
    )
}

function AccordionParticipantsItem({ index, table, children, startsOpen }: AccordionParticipantsItemProps) {
    const visibleParticipantsCount = table.rows.length
    const totalParticipantCount = table.num_participants;
    const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;

    const [isActive, setIsActive] = useState(startsOpen || visibleParticipantsCount > 0);
    const handleClick = () => setIsActive(!isActive);
  
    return (
      <>
        <AccordionTitle
            active={isActive}
            onClick={handleClick}
            styleName="title"
        >
            <Icon name="dropdown" />
            { table.title ?? 'Participants' }
            <ParticipantCounter
                styleName="participants-count-wrapper"
                totalCount={totalParticipantCount}
                hiddenCount={hiddenParticipantsCount}
            />
        </AccordionTitle>
        <AccordionContent active={isActive} key={`c${index}`}>
            { children ?? <ParticipantTable table={table} /> }
        </AccordionContent>
      </>
    );
  }

export default function ParticipantListAccordion({ tables }: ParticipantListAccordionProps) {
    console.log(tables.length)
    return (
        tables.length == 1 && tables[0].title
            ? <ParticipantTable table={ tables[0] } title="All Participants" startsOpen={true} />
            : (
                <Accordion styled fluid>
                    {
                        tables.map((table: any, i: number) => (
                            <AccordionParticipantsItem key={i} index={i} table={table} startsOpen={tables.length == 1}/>
                        ))
                    }
                </Accordion>
            )
    );
}
