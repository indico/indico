declare module 'indico-url:*' {
  function buildUrl(
    args: Record<string, any>,
    fragment?: string,
    converters?: Record<string, (value: any) => string>
  ): string;

  namespace buildUrl {
    function match(
      path: string,
      unconverters?: Record<string, (value: string) => any>
    ): Record<string, string | number>;
  }

  export default buildUrl;
}
