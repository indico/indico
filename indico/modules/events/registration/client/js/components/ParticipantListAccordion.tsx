// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import { Param, Plural, PluralTranslate, Singular } from "indico/react/i18n";
import React, { HTMLAttributes, useState } from "react"
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
} from "semantic-ui-react"
import { Translate } from "react-jsx-i18n";

import "./ParticipantListAccordion.module.scss";


interface TableObj {
    headers: string[];
    rows: Array<{
        checked_in: boolean;
        columns: Array<{ text: string; is_picture: boolean; sort_key: string | null }>;
    }>;
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
    collapsible?: boolean;
    title?: string;
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
                />{" "}
                participant registered anonymously.
            </Singular>
            <Plural>
                <Param
                    name="anonymous-participants-count"
                    value={count}
                />{" "}
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

    type sortDirectionType = "ascending" | "descending" | null;

    const [sortColumn, setSortColumn] = useState<number | null>(null);
    const [sortDirection, setSortDirection] = useState<sortDirectionType>(null);
    const [sortedRows, setSortedRows] = useState([...table.rows]);

    const handleSort = (columnIndex: number) => {
        const currentSortColumn = sortColumn === columnIndex ? sortColumn : columnIndex;

        let directions: Record<sortDirectionType, sortDirectionType> = {
            [ null as any ]: "ascending",
            "ascending": "descending",
            "descending": null
        }
    
        let direction: sortDirectionType = sortColumn === columnIndex
            ? ((directions[sortDirection]))
            : "ascending";

        const sortedData = direction == null ? [...table.rows] : [...sortedRows].sort((a, b) => {
            const textA = a.columns[columnIndex].text.toLowerCase();
            const textB = b.columns[columnIndex].text.toLowerCase();
    
            if (textA < textB) return direction === "ascending" ? -1 : 1;
            if (textA > textB) return direction === "ascending" ? 1 : -1;

            return 0;
        });

        setSortColumn(currentSortColumn);
        setSortDirection(direction);
        setSortedRows(sortedData);
    };
    

    return (
        visibleParticipantsCount > 0 ? (
            <Table fixed celled sortable className="table">
                <TableHeader>
                    <TableRow className="table-row">
                        {table.headers.map((headerText: string, j: number) => (
                            <TableHeaderCell key={j} width={1} sorted={sortColumn === j ? sortDirection : undefined} onClick={() => handleSort(j)}>
                                {headerText}
                            </TableHeaderCell>
                        ))}
                    </TableRow>
                </TableHeader>
    
                <TableBody>
                    { sortedRows.map((row, j: number) => (
                        <TableRow key={j} className="table-row">
                        { row.columns.map((col: { text: string, is_picture: boolean }, k: number) => (
                            <TableCell key={`${j}-${k}`} title={ col.text }>
                                { col.is_picture
                                    ? <img src={col.text} className="cell-img" />
                                    : col.text
                                }
                                
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

function AccordionParticipantsItem({ index, table, children, collapsible=true }: AccordionParticipantsItemProps) {
    const visibleParticipantsCount = table.rows.length
    const totalParticipantCount = table.num_participants;
    const hiddenParticipantsCount = totalParticipantCount - visibleParticipantsCount;

    const [isActive, setIsActive] = useState(!collapsible || visibleParticipantsCount > 0);
    const handleClick = () => setIsActive(!isActive);
  
    return (
      <>
        <AccordionTitle
            active={isActive}
            onClick={collapsible ? handleClick : undefined}
            styleName="title"
        >
            { collapsible && <Icon name="dropdown" /> }
            <p>
                { table.title ?? <Translate>Participants</Translate> }
            </p>
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
    return (
        <Accordion styled fluid>
            { tables.length == 1 // Case of no participants is handled in Jinja now
                ? <AccordionParticipantsItem table={tables[0]} index={1} startsOpen={true} collapsible={false} />
                : tables.map((table: any, i: number) => (
                    <AccordionParticipantsItem key={i} index={i} table={table} />
                ))
            }
        </Accordion>
    );
}
