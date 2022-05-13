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
    removeItems: !images && ['imageUpload'],
  },
  removePlugins: !images && [
    'AutoImage',
    'Image',
    'ImageCaption',
    'ImageInsert',
    'ImageStyle',
    'ImageToolbar',
    'ImageUpload',
    'MediaEmbed',
  ],
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
