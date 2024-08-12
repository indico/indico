// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import { Param, Plural, PluralTranslate, Singular } from 'indico/react/i18n';
import React, { useState } from 'react'
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
} from 'semantic-ui-react'


interface ParticipantListAccordionProps {
    tables: any
}

interface AccordionItemProps {
    index: number;
    table: any;
}

function AccordionItem({ index, table }: AccordionItemProps) {
    const [isActive, setIsActive] = useState(true);
    const hiddenParticipantsCount = table.num_participants - table.rows.length;
  
    const handleClick = () => {
      setIsActive(!isActive);
    };
  
    return (
      <>
        <AccordionTitle
          active={isActive}
          onClick={handleClick}
        >
          <Icon name="dropdown" />
          {table.title} ({table.num_participants})
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
            
            { (hiddenParticipantsCount > 0 && table.num_participants != hiddenParticipantsCount) &&
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
    <Accordion styled className="accordion">
    {tables.map((table: any, i: number) => (
        <AccordionItem key={i} index={i} table={table} />
    ))}
    </Accordion>
);
}
