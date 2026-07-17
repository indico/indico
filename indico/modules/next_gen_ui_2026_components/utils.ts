import React from 'react';

export type NativeProps<
  Tag extends keyof React.JSX.IntrinsicElements,
  Omitted extends string = never,
> = Omit<React.ComponentPropsWithoutRef<Tag>, Omitted>;

export function guardDisabledClick<E extends HTMLElement>(
  disabled: boolean | undefined,
  onClick: ((event: React.MouseEvent<E>) => void) | undefined,
  loading?: boolean | undefined
) {
  return (event: React.MouseEvent<E>) => {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  };
}

export function disabledLoadingAnchorProps(
  disabled: boolean | undefined,
  href?: string,
  tabIndex?: number,
  loading?: boolean | undefined
) {
  if (href === undefined) {
    return {
      disabled: disabled || loading || undefined,
      'aria-disabled': disabled || loading || undefined,
      tabIndex: disabled || loading ? -1 : tabIndex,
      'aria-busy': loading || undefined,
    };
  }
  return {
    href: disabled || loading ? undefined : href,
    'aria-disabled': disabled || loading || undefined,
    tabIndex: disabled || loading ? -1 : tabIndex,
  };
}
