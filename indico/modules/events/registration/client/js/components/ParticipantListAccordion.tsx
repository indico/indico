import React, { useState } from 'react'
import {
  AccordionTitle,
  AccordionContent,
  Accordion,
  Icon,
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

    console.log('tablesss')
    console.log(tables)
  
    return (
        <div>
            Hola
            <Accordion styled>
                {
                    tables.map((table, i) => (
                        <div>
                            <p>{ i }</p>
                            <p>{ table }</p>
                        </div>
                        // <div>
                        //     <AccordionTitle
                        //         active={activeIndex === 0}
                        //         index={0}
                        //         onClick={handleClick}
                        //     >
                        //     <Icon name='dropdown' />
                        //     What is a dog? { table }
                        //     </AccordionTitle>
                        //     <AccordionContent active={activeIndex === 0}>
                        //     <p>
                        //         A dog is a type of domesticated animal. Known for its loyalty and
                        //         faithfulness, it can be found as a welcome guest in many households
                        //         across the world.
                        //     </p>
                        //     </AccordionContent>
                        // </div>
                    ))
                }
            </Accordion>
        </div>
    //     <AccordionTitle
    //       active={activeIndex === 0}
    //       index={0}
    //       onClick={handleClick}
    //     >
    //       <Icon name='dropdown' />
    //       What is a dog? { title }
    //     </AccordionTitle>
    //     <AccordionContent active={activeIndex === 0}>
    //       <p>
    //         A dog is a type of domesticated animal. Known for its loyalty and
    //         faithfulness, it can be found as a welcome guest in many households
    //         across the world.
    //       </p>
    //     </AccordionContent>
  
    //     <AccordionTitle
    //       active={activeIndex === 1}
    //       index={1}
    //       onClick={handleClick}
    //     >
    //       <Icon name='dropdown' />
    //       What kinds of dogs are there?
    //     </AccordionTitle>
    //     <AccordionContent active={activeIndex === 1}>
    //       <p>
    //         There are many breeds of dogs. Each breed varies in size and
    //         temperament. Owners often select a breed of dog that they find to be
    //         compatible with their own lifestyle and desires from a companion.
    //       </p>
    //     </AccordionContent>
  
    //     <AccordionTitle
    //       active={activeIndex === 2}
    //       index={2}
    //       onClick={handleClick}
    //     >
    //       <Icon name='dropdown' />
    //       How do you acquire a dog?
    //     </AccordionTitle>
    //     <AccordionContent active={activeIndex === 2}>
    //       <p>
    //         Three common ways for a prospective owner to acquire a dog is from
    //         pet shops, private owners, or shelters.
    //       </p>
    //       <p>
    //         A pet shop may be the most convenient way to buy a dog. Buying a dog
    //         from a private owner allows you to assess the pedigree and upbringing
    //         of your dog before choosing to take it home. Lastly, finding your dog
    //         from a shelter helps give a good home to a dog who may not find one
    //         so readily.
    //       </p>
    //     </AccordionContent>
    //   </Accordion>
    )
  }
  