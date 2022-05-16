// TODO: upload adapter
// TODO: simple version?

// TODO: move to CSS
export function onReady(editor, options) {
  const {width, height} = options;
  editor.editing.view.change(writer => {
    writer.setStyle('height', `${height || 400}px`, editor.editing.view.document.getRoot());
    if (width) {
      writer.setStyle('width', `${width}px`, editor.editing.view.document.getRoot());
    }
  });
}

export const getConfig = ({images = false} = {}) => ({
  language: 'en_GB',
  fontFamily: {
    options: [
      'Sans Serif/"Liberation Sans", sans-serif',
      'Serif/"Liberation Serif", serif',
      'Monospace/"Liberation Mono", monospace',
    ],
  },
  toolbar: {
    shouldNotGroupWhenFull: false,
    items: [
      'heading',
      '|',
      'bold',
      'italic',
      'strikethrough',
      '|',
      'fontColor',
      'removeFormat',
      '|',
      'bulletedList',
      'numberedList',
      'outdent',
      'indent',
      '|',
      'link',
      images && 'imageInsert',
      'insertTable',
      '|',
      'blockQuote',
      'code',
      'horizontalLine',
      '|',
      'findAndReplace',
      'undo',
      'redo',
      '|',
      'sourceEditing',
    ].filter(Boolean),
  },
  plugins: [
    'Autoformat',
    images && 'AutoImage',
    'AutoLink',
    'BlockQuote',
    'Bold',
    'CloudServices',
    'Code',
    'CodeBlock',
    'Essentials',
    'FindAndReplace',
    'FontColor',
    'GeneralHtmlSupport',
    'Heading',
    'HorizontalLine',
    images && 'Image',
    images && 'ImageCaption',
    images && 'ImageInsert',
    images && 'ImageStyle',
    images && 'ImageToolbar',
    // images && 'ImageUpload',
    'Indent',
    'IndentBlock',
    'Italic',
    'Link',
    'List',
    'Markdown',
    images && 'MediaEmbed',
    'Paragraph',
    'PasteFromOffice',
    'RemoveFormat',
    'SourceEditing',
    'Strikethrough',
    'Table',
    'TableToolbar',
  ].filter(Boolean),
  htmlSupport: {
    allow: [
      {name: 'dl'},
      {name: 'dt'},
      {name: 'dd'},
      {name: 'div'},
      {name: 'span'},
      {name: 'pre'},
      {
        name: 'img',
        attributes: {
          usemap: true,
        },
      },
      {
        name: 'area',
        attributes: true,
      },
      {
        name: 'map',
        attributes: true,
      },
    ],
  },
});
