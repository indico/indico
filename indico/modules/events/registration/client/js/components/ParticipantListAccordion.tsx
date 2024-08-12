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
} from 'semantic-ui-react'


import './ParticipantListAccordion.module.scss';

interface ParticipantListAccordionProps {
    tables: any
}

interface AccordionItemProps {
    index: number;
    table: any;
}


interface ParticipantCounterProps extends HTMLAttributes<HTMLSpanElement> {
    styleName?: string;
    visibleCount?: number;
    hiddenCount?: number;
}

const ParticipantCountTranslationHidden: React.FC<{ count: number }> = ({ count }) => {
    return (
        <PluralTranslate count={count}>
            <Param
                name="participants-count"
                value={count}
            />{' '}
            <Singular>
                participant registered anonymously
            </Singular>
            <Plural>
                participants registered anonymously
            </Plural>
        </PluralTranslate>
    )
}

const ParticipantCountTranslationVisible: React.FC<{ count: number }> = ({ count }) => {
    return (
        <PluralTranslate count={count}>
            <Singular>
                participant registered
            </Singular>
            <Plural>
                participants registered
            </Plural>
        </PluralTranslate>
    )
}
  
const ParticipantCounter: React.FC<ParticipantCounterProps> = ({ styleName, visibleCount, hiddenCount, ...props }) => {
    return (
        <div className={styleName} {...props}>
            { visibleCount > 0 &&
                <Popup
                    position="bottom center"
                    content={ <ParticipantCountTranslationVisible count={visibleCount} /> }
                    trigger={
                        <span title="hey">
                            {visibleCount} <Icon name="user" />
                        </span>
                    }
                />
            }
            { hiddenCount > 0 && 
                <Popup
                    position="bottom center"
                    content={ <ParticipantCountTranslationHidden count={hiddenCount} /> }
                    trigger={
                        <span title="hey">
                            {hiddenCount} <Icon name="user outline" />
                        </span>
                    }
                />
            }
        </div>
    );
};

function AccordionItem({ index, table }: AccordionItemProps) {
    const visibleParticipantsCount = table.rows.length
    const hiddenParticipantsCount = table.num_participants - visibleParticipantsCount;
    const hasInvisibleParticipants = hiddenParticipantsCount > 0

    const [isActive, setIsActive] = useState(visibleParticipantsCount > 0);
    const handleClick = () => {
        setIsActive(!isActive);
    };

  
    return (
      <>
        <AccordionTitle
            active={isActive}
            onClick={handleClick}
            styleName="title"
        >
            <Icon name="dropdown" />
            {table.title} ({table.num_participants})
            <ParticipantCounter
                styleName="participants-count-wrapper"
                visibleCount={visibleParticipantsCount}
                hiddenCount={hiddenParticipantsCount}
            >
                <Icon name="dropdown" />
            </ParticipantCounter>
        </AccordionTitle>
        <AccordionContent active={isActive} key={`c${index}`}>
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
                            <PluralTranslate count={hiddenParticipantsCount}>
                                <Singular>
                                    <Param
                                        name="visible-participants"
                                        value={hiddenParticipantsCount}
                                        />{' '}
                                    participant registered anonymously
                                </Singular>
                                <Plural>
                                    <Param
                                        name="visible-participants"
                                        value={hiddenParticipantsCount}
                                        />{' '}
                                    participants registered anonymously
                                </Plural>
                            </PluralTranslate>
                        </TableHeaderCell>
                    </TableRow>
                </TableFooter>
            }
          </Table>
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
