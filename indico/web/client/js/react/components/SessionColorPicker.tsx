// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Button, Popup} from 'semantic-ui-react';

import {FinalField, FormFieldAdapter} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';
import './SessionColorPicker.module.scss';

interface ColorSchema {
  text: string;
  background: string;
}

interface SessionColorPickerProps {
  value: ColorSchema | null;
  onChange: (color: ColorSchema) => void;
  trigger: React.ReactNode;
}

const AVAILABLE_COLORS: ColorSchema[] = [
  {text: '#1D041F', background: '#EEE0EF'},
  {text: '#253F08', background: '#E3F2D3'},
  {text: '#1F1F02', background: '#FEFFBF'},
  {text: '#202020', background: '#DFE555'},
  {text: '#1F1D04', background: '#FFEC1F'},
  {text: '#0F264F', background: '#DFEBFF'},
  {text: '#EFF5FF', background: '#0D316F'},
  {text: '#F1FFEF', background: '#1A3F14'},
  {text: '#FFFFFF', background: '#5F171A'},
  {text: '#272F09', background: '#D9DFC3'},
  {text: '#FFEFFF', background: '#4F144E'},
  {text: '#FFEDDF', background: '#6F390D'},
  {text: '#021F03', background: '#8EC473'},
  {text: '#03070F', background: '#92B6DB'},
  {text: '#151515', background: '#DFDFDF'},
  {text: '#1F1100', background: '#ECC495'},
  {text: '#0F0202', background: '#B9CBCA'},
  {text: '#0D1E1F', background: '#C2ECEF'},
  {text: '#000000', background: '#D0C296'},
  {text: '#202020', background: '#EFEBC2'},
];

export default function SessionColorPicker({value, onChange, trigger}: SessionColorPickerProps) {
  const [open, setOpen] = useState(false);

  const makePickHandler = (color: ColorSchema) => () => {
    onChange(color);
    setOpen(false);
  };

  return (
    <Popup
      on="click"
      open={open}
      trigger={trigger}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      content={
        <div styleName="choice-box">
          {AVAILABLE_COLORS.map(color => (
            <Button
              key={color.background}
              type="button"
              onClick={makePickHandler(color)}
              style={{color: color.text, backgroundColor: color.background}}
              icon="tint"
              styleName={toClasses({
                choice: true,
                selected: color.background === (value ? value.background : undefined),
              })}
              circular
            />
          ))}
        </div>
      }
    />
  );
}

interface SessionColorPickerAdapterProps {
  input: {
    value: ColorSchema | null;
    onChange: (color: ColorSchema) => void;
  };
}

const SessionColorPickerAdapter: React.FC<SessionColorPickerAdapterProps> = ({input, ...rest}) => (
  <FormFieldAdapter
    input={input}
    {...rest}
    as={SessionColorPicker}
    trigger={
      <Button
        type="button"
        icon="paint brush"
        style={{color: input.value?.text, backgroundColor: input.value?.background}}
        content={Translate.string('Choose')}
        circular
      />
    }
  />
);

interface FinalSessionColorPickerProps {
  name: string;
}

export function FinalSessionColorPicker({name, ...rest}: FinalSessionColorPickerProps) {
  return <FinalField name={name} adapter={SessionColorPickerAdapter} {...rest} />;
}
