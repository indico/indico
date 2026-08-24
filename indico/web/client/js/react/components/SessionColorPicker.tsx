// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
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

export const AVAILABLE_COLORS: ColorSchema[] = [
  {text: '#1d041f', background: '#eee0ef'},
  {text: '#253f08', background: '#e3f2d3'},
  {text: '#1f1f02', background: '#feffbf'},
  {text: '#202020', background: '#dfe555'},
  {text: '#1f1d04', background: '#ffec1f'},
  {text: '#0f264f', background: '#dfebff'},
  {text: '#eff5ff', background: '#0d316f'},
  {text: '#f1ffef', background: '#1a3f14'},
  {text: '#ffffff', background: '#5f171a'},
  {text: '#272f09', background: '#d9dfc3'},
  {text: '#ffefff', background: '#4f144e'},
  {text: '#ffeddf', background: '#6f390d'},
  {text: '#021f03', background: '#8ec473'},
  {text: '#03070f', background: '#92b6db'},
  {text: '#151515', background: '#dfdfdf'},
  {text: '#1f1100', background: '#ecc495'},
  {text: '#0f0202', background: '#b9cbca'},
  {text: '#0d1e1f', background: '#c2ecef'},
  {text: '#000000', background: '#d0c296'},
  {text: '#202020', background: '#efebc2'},
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
        style={{
          color: input.value ? input.value.text : undefined,
          backgroundColor: input.value ? input.value.background : undefined,
        }}
        content={Translate.string('Choose')}
        circular
      />
    }
  />
);

interface FinalSessionColorPickerProps {
  name: string;
  label?: string;
}

export function FinalSessionColorPicker({name, ...rest}: FinalSessionColorPickerProps) {
  return <FinalField name={name} adapter={SessionColorPickerAdapter} {...rest} />;
}
