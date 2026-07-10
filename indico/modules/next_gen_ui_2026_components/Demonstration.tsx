// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';

import './IndicoUIProvider.scss';
import Button from './button/Button';
import {Icon} from './icon/Icon';

const colors = ['primary', 'gray', 'success', 'warning', 'error'] as const;
const colorsWithWhite = ['primary', 'gray', 'success', 'warning', 'error', 'white'] as const;
const sizes = ['xs', 'sm', 'md', 'lg', 'xl'] as const;
const iconVariants = ['light', 'solid', 'dark', 'plain', 'compact'] as const;
const iconVariantsRestricted = ['light', 'solid', 'dark'] as const;
const iconVariantsRestrictedForWhite = ['plain', 'compact'] as const;
// const buttonOpacity = ['opaque', 'transparent'] as const;
const buttonVariant = ['solid', 'light', 'white'] as const;

export function Demonstration() {
  const [isIconExpanded, setIsIconExpanded] = useState(false);
  const [isButtonExpanded, setIsButtonExpanded] = useState(false);
  const [isTagExpanded, setIsTagExpanded] = useState(false);
  return (
    <div
      className="indico-ui"
      role="none"
      style={{
        padding: '24px',
        backgroundImage:
          'radial-gradient(#EEEEEE 2px, transparent 2px), radial-gradient(#EEEEEE 2px, transparent 2px)',
        backgroundSize: '17px 17px',
        backgroundPosition: '0 0, 8.5px 8.5px',
        backgroundColor: '#E5E5EE',
        borderRadius: '8px',
        marginTop: '24px',
      }}
    >
      <h1 style={{color: '#979a9c'}}>Indico UI Components Demonstration</h1>
      <details>
        <summary
          style={{cursor: 'pointer', outline: 'none', userSelect: 'none'}}
          onClick={() => setIsIconExpanded(!isIconExpanded)}
        >
          <h2
            style={{
              color: '#005f8d',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              margin: 0,
            }}
          >
            Icons
            <Icon
              icon={isIconExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
              color="primary"
              variant="plain"
              size="xs"
            />
          </h2>
        </summary>
        <section>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)'}}>
            {iconVariants.slice(0, 3).map(variant =>
              colors.map(color =>
                sizes.map(size => (
                  <div
                    key={`${variant}-${color}-${size}-square`}
                    style={{
                      padding: '12px',
                      borderRadius: '4px',
                      alignItems: 'center',
                      justifyContent: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Icon icon="fas:pen" variant={variant} color={color} size={size} />
                    <div
                      style={{
                        fontSize: '11px',
                        color: '#666',
                        marginTop: '8px',
                        textAlign: 'center',
                      }}
                    >
                      {variant} • {color} • {size}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </section>
        <section>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)'}}>
            {iconVariantsRestricted.map(variant =>
              colors.map(color =>
                sizes.map(size => (
                  <div
                    key={`${variant}-${color}-${size}-rounded`}
                    style={{
                      padding: '12px',
                      borderRadius: '4px',
                      alignItems: 'center',
                      justifyContent: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Icon icon="fas:pen" variant={variant} color={color} size={size} rounded />
                    <div
                      style={{
                        fontSize: '11px',
                        color: '#666',
                        marginTop: '8px',
                        textAlign: 'center',
                      }}
                    >
                      {variant} • {color} • {size} • rounded
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </section>
        <section>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)'}}>
            {iconVariantsRestrictedForWhite.map(variant =>
              colorsWithWhite.map(color =>
                sizes.map(size => (
                  <div
                    key={`${variant}-${color}-${size}`}
                    style={{
                      padding: '12px',
                      borderRadius: '4px',
                      alignItems: 'center',
                      justifyContent: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Icon icon="fas:pen" variant={variant} color={color} size={size} />
                    <div
                      style={{
                        fontSize: '11px',
                        color: '#666',
                        marginTop: '8px',
                        textAlign: 'center',
                      }}
                    >
                      {variant} • {color} • {size}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </section>
      </details>
      <details>
        <summary
          style={{cursor: 'pointer', outline: 'none', userSelect: 'none'}}
          onClick={() => setIsButtonExpanded(!isButtonExpanded)}
        >
          <h2
            style={{
              color: '#005f8d',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              margin: 0,
            }}
          >
            Buttons
            <Icon
              icon={isButtonExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
              color="primary"
              variant="plain"
              size="xs"
            />
          </h2>
        </summary>
        <section>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)'}}>
            {buttonVariant.map(variant =>
              colors.map(color =>
                sizes.map(size => (
                  <div
                    key={`${'opaque'}-${variant}-${color}-${size}-square`}
                    style={{
                      padding: '12px',
                      borderRadius: '4px',
                      alignItems: 'center',
                      justifyContent: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Button color={color} variant={variant} size={size}>
                      Button
                    </Button>
                    <div
                      style={{
                        fontSize: '11px',
                        color: '#666',
                        marginTop: '8px',
                        textAlign: 'center',
                      }}
                    >
                      {variant} • {color} • {size}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </section>
        <section>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)'}}>
            {buttonVariant.map(variant =>
              colors.map(color =>
                sizes.map(size => (
                  <div
                    key={`${'opaque'}-${variant}-${color}-${size}-square`}
                    style={{
                      padding: '12px',
                      borderRadius: '4px',
                      alignItems: 'center',
                      justifyContent: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Button color={color} variant={variant} size={size} opacity="opaque">
                      Button
                    </Button>
                    <div
                      style={{
                        fontSize: '11px',
                        color: '#666',
                        marginTop: '8px',
                        textAlign: 'center',
                      }}
                    >
                      {variant} • opaque • {color} • {size}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </section>
        <section>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)'}}>
            {colors.map(color =>
              sizes.map(size => (
                <div
                  key={`${'transparent'}-${color}-${size}-square`}
                  style={{
                    padding: '12px',
                    borderRadius: '4px',
                    alignItems: 'center',
                    justifyContent: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <Button color={color} size={size} opacity="transparent">
                    Button
                  </Button>
                  <div
                    style={{
                      fontSize: '11px',
                      color: '#666',
                      marginTop: '8px',
                      textAlign: 'center',
                    }}
                  >
                    transparent • {color} • {size}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </details>
      <details>
        <summary
          style={{cursor: 'pointer', outline: 'none', userSelect: 'none'}}
          onClick={() => setIsTagExpanded(!isTagExpanded)}
        >
          <h2
            style={{
              color: '#005f8d',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              margin: 0,
            }}
          >
            Tags
            <Icon
              icon={isTagExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
              color="primary"
              variant="plain"
              size="xs"
            />
          </h2>
        </summary>
      </details>
    </div>
  );
}
