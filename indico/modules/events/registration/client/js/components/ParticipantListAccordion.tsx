import React, { useState } from 'react'
import {
  AccordionTitle,
  AccordionContent,
  Accordion,
  Icon,
  TableRow,
  TableHeaderCell,
  TableHeader,
  TableFooter,
  TableCell,
  TableBody,
  MenuItem,
  Label,
  Menu,
  Table,
} from 'semantic-ui-react'
import { AccordionTitleProps } from 'semantic-ui-react/dist/commonjs/modules/Accordion/AccordionTitle'


interface ParticipantListAccordionProps {
    tables: any
}

export default function ParticipantListAccordion({ tables }: ParticipantListAccordionProps) {
    const [activeIndex, setActiveIndex] = useState<number>(0)
  
    const handleClick = (
        e: React.MouseEvent<HTMLDivElement, MouseEvent>,
        titleProps: AccordionTitleProps
    ) => {
        const { index } = titleProps
        const newIndex = activeIndex === index ? -1 : index
        setActiveIndex(newIndex as number)
    }

    return (
        <Accordion styled>
            { tables.map((table, i) => (
                <React.Fragment key={i}>
                    <AccordionTitle
                        active={activeIndex === i}
                        index={i}
                        onClick={handleClick}
                        key={`t${i}`}
                    >
                        <Icon name='dropdown' />
                        { table.title } ({ table.num_participants })
                    </AccordionTitle>
                    <AccordionContent active={activeIndex === i} key={`c${i}`}>
                        <Table celled>
                            <TableHeader>
                                <TableRow>
                                    { table.headers.map((headerText, j) => (
                                        <TableHeaderCell key={`${i}-${j}`}>{ headerText }</TableHeaderCell>
                                    ))}
                                </TableRow>
                            </TableHeader>

                            <TableBody>
                                { table.rows.map((row, j) => (
                                    <TableRow key={`${i}-${j}`}>
                                        { row.columns.map((col, k) => (
                                            <TableCell key={`${i}-${j}-${k}`}>{ col.text }</TableCell>
                                        ))}
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </AccordionContent>
                </React.Fragment>)
            )}
        </Accordion>
    )
  }
