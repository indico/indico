// Justification of this file found in issue below
// https://github.com/gajus/babel-plugin-react-css-modules/issues/292

declare namespace React {
  interface Attributes {
    styleName?: string;
  }
  interface HTMLAttributes<T> {
    styleName?: string;
  }
  interface SVGAttributes<T> {
    styleName?: string;
  }
}
