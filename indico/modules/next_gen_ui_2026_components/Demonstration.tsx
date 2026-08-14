// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';

import './Demonstration.module.scss';
import {Button} from './button/Button';
import {Icon} from './icon/Icon';
import {Tag} from './tag/Tag';

const colors = ['primary', 'gray', 'success', 'warning', 'error'] as const;
const colorsWithWhite = ['primary', 'gray', 'success', 'warning', 'error', 'white'] as const;
const sizes = ['xs', 'sm', 'md', 'lg', 'xl'] as const;
const iconSizes = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl', 'xxxl', 'xxxxl'] as const;
const iconVariants = ['light', 'solid', 'transparent'] as const;
const iconVariantsRestricted = ['light', 'solid'] as const;
const iconVariantsRestrictedForWhite = ['transparent'] as const;
const buttonAttributes = [
  '',
  'animated',
  'compact',
  'compact icon=fas:calendar',
  'icon=fas:calendar',
  'outlined',
  'disabled',
  'opaque',
  'disabled opaque',
] as const;

const buttonAttributesNoOpaque = [
  '',
  'animated',
  'compact',
  'compact icon=fas:calendar',
  'icon=fas:calendar',
  'outlined',
  'disabled',
] as const;

const tagAttributes = [
  '',
  'outlined',
  'rounded',
  'icon=fas:calendar',
  'icon=fas:calendar iconPosition=right',
  'opaque',
] as const;
const textWeights = ['regular', 'bold'] as const;

export function Demonstration() {
  const [isIconExpanded, setIsIconExpanded] = useState(false);
  const [isButtonExpanded, setIsButtonExpanded] = useState(true);
  const [isTagExpanded, setIsTagExpanded] = useState(false);
  return (
    <div styleName="wrapper-demonstration">
      <div styleName="background-colorful">
        <h1>Indico UI Components Demonstration</h1>
        {/* ICON */}
        <details>
          <summary onClick={() => setIsIconExpanded(!isIconExpanded)}>
            <h2>
              Icons
              <Icon
                icon={isIconExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
                color="primary"
                variant="transparent"
                size="xs"
              />
            </h2>
          </summary>
          <section>
            <div className="grid-8">
              {iconVariants.map(variant =>
                colors.map(color =>
                  iconSizes.map(size => (
                    <div
                      key={`${variant}-${color}-${size}-square`}
                      styleName="demo-item align-center"
                    >
                      <Icon icon="fas:pen" variant={variant} color={color} size={size} />
                      <div styleName="demo-label">
                        variant: {variant} • color: {color} • size: {size}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <section>
            <div className="grid-8">
              {iconVariantsRestricted.map(variant =>
                colors.map(color =>
                  iconSizes.map(size => (
                    <div
                      key={`${variant}-${color}-${size}-rounded`}
                      styleName="demo-item align-center"
                    >
                      <Icon icon="fas:pen" variant={variant} color={color} size={size} rounded />
                      <div styleName="demo-label">
                        variant: {variant} • color: {color} • size: {size} • rounded
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <section>
            <div className="grid-8">
              {iconVariantsRestrictedForWhite.map(variant =>
                colorsWithWhite.map(color =>
                  iconSizes.map(size => (
                    <div key={`${variant}-${color}-${size}`} styleName="demo-item align-center">
                      <Icon icon="fas:pen" variant={variant} color={color} size={size} />
                      <div styleName="demo-label">
                        variant: {variant} • color: {color} • size: {size}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <section>
            <div className="grid-8">
              {iconVariantsRestrictedForWhite.map(variant =>
                colorsWithWhite.map(color =>
                  iconSizes.map(size => (
                    <div
                      key={`${variant}-${color}-${size}-compact`}
                      styleName="demo-item align-center"
                    >
                      <Icon icon="fas:pen" variant={variant} color={color} size={size} compact />
                      <div styleName="demo-label">
                        variant: {variant} • color: {color} • size: {size} • compact
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
        </details>
        {/* BUTTON */}
        <details>
          <summary onClick={() => setIsButtonExpanded(!isButtonExpanded)}>
            <h2>
              Buttons
              <Icon
                icon={!isButtonExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
                color="primary"
                variant="transparent"
                size="xs"
              />
            </h2>
          </summary>
          <h3> Button text Weights</h3>
          <div className="grid-5">
            {textWeights.map(textWeight =>
              sizes.map(size => (
                <div
                  key={`${'solid'}-${'primary'}-${size}-${textWeight}-square`}
                  styleName="demo-item align-center"
                >
                  <Button color="primary" variant="solid" size={size} textWeight={textWeight}>
                    Button
                  </Button>
                  <div styleName="demo-label">
                    solid • primary • {size} • {textWeight}
                  </div>
                </div>
              ))
            )}
          </div>
          <h3> Rounded </h3>
          <div className="grid-5">
            {sizes.map(size => (
              <div
                key={`${'solid'}-${'primary'}-${size}-rounded`}
                styleName="demo-item align-center"
              >
                <Button color="primary" variant="solid" size={size} rounded>
                  Button
                </Button>
                <div styleName="demo-label">solid • primary • {size} • rounded</div>
              </div>
            ))}
          </div>
          <h3> Circular </h3>
          <div className="grid-5">
            {sizes.map(size => (
              <div
                key={`${'solid'}-${'primary'}-${size}-circular`}
                styleName="demo-item align-center"
              >
                <Button color="primary" variant="solid" size={size} circular>
                  Button
                </Button>
                <div styleName="demo-label">solid • primary • {size} • circular</div>
              </div>
            ))}
          </div>
          <h3> Icon only </h3>
          <div className="grid-5">
            {sizes.map(size => (
              <div
                key={`${'solid'}-${'primary'}-${size}-icon-only`}
                styleName="demo-item align-center"
              >
                <Button
                  color="primary"
                  variant="solid"
                  size={size}
                  icon="fas:calendar"
                  iconOnly
                  aria-label="Calendar"
                />
                <div styleName="demo-label">solid • primary • {size} • icon only</div>
              </div>
            ))}
          </div>
          <h3> Icon only rounded</h3>
          <div className="grid-5">
            {sizes.map(size => (
              <div
                key={`${'solid'}-${'primary'}-${size}-icon-only-rounded`}
                styleName="demo-item align-center"
              >
                <Button
                  color="primary"
                  variant="solid"
                  size={size}
                  icon="fas:calendar"
                  iconOnly
                  rounded
                  aria-label="Calendar"
                />
                <div styleName="demo-label">solid • primary • {size} • icon only rounded</div>
              </div>
            ))}
          </div>
          <h3> Icon only circular</h3>
          <div className="grid-5">
            {sizes.map(size => (
              <div
                key={`${'solid'}-${'primary'}-${size}-icon-only-circular`}
                styleName="demo-item align-center"
              >
                <Button
                  color="primary"
                  variant="solid"
                  size={size}
                  icon="fas:calendar"
                  iconOnly
                  circular
                  aria-label="Calendar"
                />
                <div styleName="demo-label">solid • primary • {size} • icon only circular</div>
              </div>
            ))}
          </div>
          <h3> Icon only squared</h3>
          <div className="grid-5">
            {sizes.map(size => (
              <div
                key={`${'solid'}-${'primary'}-${size}-icon-only-squared`}
                styleName="demo-item align-center"
              >
                <Button
                  color="primary"
                  variant="solid"
                  size={size}
                  icon="fas:calendar"
                  iconOnly
                  squared
                  aria-label="Calendar"
                />
                <div styleName="demo-label">solid • primary • {size} • icon only squared</div>
              </div>
            ))}
          </div>
          <h3>Variant: Solid</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                buttonAttributes.map(attribute =>
                  sizes.map(size => (
                    <div
                      key={`${'solid'}-${color}-${size}-${attribute}-square`}
                      styleName="demo-item align-center"
                    >
                      <Button
                        color={color}
                        variant="solid"
                        size={size}
                        {...(attribute
                          ? Object.fromEntries(
                              attribute.split(' ').map(attr => {
                                const [key, value] = attr.split('=');
                                return [key, value ?? true];
                              })
                            )
                          : {})}
                      >
                        Button
                      </Button>
                      <div styleName="demo-label">
                        solid • {color} • {size} • {attribute}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <h3>Variant: Light</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                buttonAttributes.map(attribute =>
                  sizes.map(size => (
                    <div
                      key={`${'light'}-${color}-${size}-${attribute}-square`}
                      styleName="demo-item align-center"
                    >
                      <Button
                        color={color}
                        variant="light"
                        size={size}
                        {...(attribute
                          ? Object.fromEntries(
                              attribute.split(' ').map(attr => {
                                const [key, value] = attr.split('=');
                                return [key, value ?? true];
                              })
                            )
                          : {})}
                      >
                        Button
                      </Button>
                      <div styleName="demo-label">
                        light • {color} • {size} • {attribute}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <h3>Variant: White</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                buttonAttributes.map(attribute =>
                  sizes.map(size => (
                    <div
                      key={`${'white'}-${color}-${size}-${attribute}-square`}
                      styleName="demo-item align-center"
                    >
                      <Button
                        color={color}
                        variant="white"
                        size={size}
                        {...(attribute
                          ? Object.fromEntries(
                              attribute.split(' ').map(attr => {
                                const [key, value] = attr.split('=');
                                return [key, value ?? true];
                              })
                            )
                          : {})}
                      >
                        Button
                      </Button>
                      <div styleName="demo-label">
                        white • {color} • {size} • {attribute}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <h3>Variant: Transparent</h3>
          <section>
            <div className="grid-5">
              {colorsWithWhite.map(color =>
                buttonAttributesNoOpaque.map(attribute =>
                  sizes.map(size => {
                    return (
                      <div
                        key={`${'transparent'}-${color}-${size}-${attribute}-square`}
                        styleName="demo-item align-center"
                      >
                        <Button
                          color={color}
                          variant="transparent"
                          size={size}
                          {...(attribute
                            ? Object.fromEntries(
                                attribute.split(' ').map(attr => {
                                  const [key, value] = attr.split('=');
                                  return [key, value ?? true];
                                })
                              )
                            : {})}
                        >
                          Button
                        </Button>
                        <div styleName="demo-label">
                          transparent • {color} • {size} • {attribute}
                        </div>
                      </div>
                    );
                  })
                )
              )}
            </div>
          </section>
        </details>
        <details>
          <summary
            style={{cursor: 'pointer', outline: 'none', userSelect: 'none'}}
            onClick={() => setIsTagExpanded(!isTagExpanded)}
          >
            <h2>
              Tags
              <Icon
                icon={isTagExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
                color="primary"
                variant="transparent"
                size="xs"
              />
            </h2>
          </summary>
          <h3>Variant: Solid</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                tagAttributes.map(attribute =>
                  sizes.map(size => (
                    <div
                      key={`${'solid'}-${color}-${size}-${attribute}-square`}
                      styleName="demo-item align-center"
                    >
                      <Tag
                        color={color}
                        variant="solid"
                        size={size}
                        {...(attribute
                          ? Object.fromEntries(
                              attribute.split(' ').map(attr => {
                                const [key, value] = attr.split('=');
                                return [key, value ?? true];
                              })
                            )
                          : {})}
                      >
                        29 Aug - 3 Sep
                      </Tag>
                      <div styleName="demo-label">
                        solid • {color} • {size} • {attribute}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <h3>Variant: Light</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                tagAttributes.map(attribute =>
                  sizes.map(size => (
                    <div
                      key={`${'light'}-${color}-${size}-${attribute}-square`}
                      styleName="demo-item align-center"
                    >
                      <Tag
                        color={color}
                        variant="light"
                        size={size}
                        {...(attribute
                          ? Object.fromEntries(
                              attribute.split(' ').map(attr => {
                                const [key, value] = attr.split('=');
                                return [key, value ?? true];
                              })
                            )
                          : {})}
                      >
                        29 Aug - 3 Sep
                      </Tag>
                      <div styleName="demo-label">
                        light • {color} • {size} • {attribute}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <h3>Variant: White</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                tagAttributes.slice(0, 4).map(attribute =>
                  sizes.map(size => (
                    <div
                      key={`${'white'}-${color}-${size}-${attribute}-square`}
                      styleName="demo-item align-center"
                    >
                      <Tag
                        color={color}
                        variant="white"
                        size={size}
                        {...(attribute
                          ? Object.fromEntries(
                              attribute.split(' ').map(attr => {
                                const [key, value] = attr.split('=');
                                return [key, value ?? true];
                              })
                            )
                          : {})}
                      >
                        29 Aug - 3 Sep
                      </Tag>
                      <div styleName="demo-label">
                        white • {color} • {size} • {attribute}
                      </div>
                    </div>
                  ))
                )
              )}
            </div>
          </section>
          <h3>Variant: Transparent</h3>
          <section>
            <div className="grid-5">
              {colors.map(color =>
                tagAttributes.slice(0, 4).map(attribute =>
                  sizes.map(size => {
                    return (
                      <div
                        key={`${'transparent'}-${color}-${size}-${attribute}-square`}
                        styleName="demo-item align-center"
                      >
                        <Tag
                          color={color}
                          variant="transparent"
                          size={size}
                          {...(attribute
                            ? Object.fromEntries(
                                attribute.split(' ').map(attr => {
                                  const [key, value] = attr.split('=');
                                  return [key, value ?? true];
                                })
                              )
                            : {})}
                        >
                          29 Aug - 3 Sep
                        </Tag>
                        <div styleName="demo-label">
                          transparent • {color} • {size} • {attribute}
                        </div>
                      </div>
                    );
                  })
                )
              )}
            </div>
          </section>
        </details>
      </div>
    </div>
  );
}
