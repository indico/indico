<script type="text/x-mathjax-config">

MathJax.Hub.Config({
  config: [],
  styleSheets: [],
  styles: {},
  jax: ["input/TeX","output/HTML-CSS"],
  extensions: ["tex2jax.js"],
  preJax: null,
  postJax: null,
  preRemoveClass: "MathJax_Preview",
  showProcessingMessages: true,
  messageStyle: "normal",
  displayAlign: "center",
  displayIndent: "0em",
  delayStartupUntil: "none",
  skipStartupTypeset: true,
  elements: [],
  positionToHash: false,
  showMathMenu: true,
  showMathMenuMSIE: true,

  menuSettings: {
    zoom: "None",        //  when to do MathZoom
    CTRL: false,         //    require CTRL for MathZoom?
    ALT: false,          //    require Alt or Option?
    CMD: false,          //    require CMD?
    Shift: false,        //    require Shift?
    zscale: "200%",      //  the scaling factor for MathZoom
    font: "Auto",        //  what font HTML-CSS should use
    context: "MathJax",  //  or "Browser" for pass-through to browser menu
    mpContext: false,    //  true means pass menu events to MathPlayer in IE
    mpMouse: false,      //  true means pass mouse events to MathPlayer in IE
    texHints: true       //  include class names for TeXAtom elements
  },

  errorSettings: {
    message: ["[Math Processing Error]"], // HTML snippet structure for message to use
    messageId: "MathProcessingError",     // ID of snippet for localization
    style: {color: "#CC0000", "font-style":"italic"}  // style for message
  },

  tex2jax: {
    inlineMath: [
      ['$','$']
    ],

    displayMath: [
      ['$$','$$'],
      ['\\[','\\]']
    ],

    balanceBraces: true,
    skipTags: ["script","noscript","style","textarea","pre","code"],
    ignoreClass: "tex2jax_ignore",
    processClass: "tex2jax_process",
    processEscapes: false,
    processEnvironments: true,
    processRefs: true,

    preview: "TeX"

  },

  asciimath2jax: {

    delimiters: [
      ['`','`']
    ],

    skipTags: ["script","noscript","style","textarea","pre","code"],

    ignoreClass: "asciimath2jax_ignore",

    processClass: "asciimath2jax_process",

    preview: "AsciiMath"

  },

  mml2jax: {

    preview: "alttext"

  },

  jsMath2jax: {

    preview: "TeX"

  },

  TeX: {

    TagSide: "right",

    TagIndent: ".8em",

    MultLineWidth: "85%",

    Macros: {},

    equationNumbers: {
      autoNumber: "none",  // "AMS" for standard AMS environment numbering,
      useLabelIds: true    // make element ID's use \label name rather than equation number
    },

    noErrors: {
      disabled: false,               // set to true to return to original error messages
      multiLine: true,               // false to not include original line breaks
      inlineDelimiters: ["",""],     // or use ["$","$"] or ["\\(","\\)"] to put back delimiters
      style: {
        "font-size":   "90%",
        "text-align":  "left",
        "color":       "black",
        "padding":     "1px 3px",
        "border":      "1px solid"
      }
    },

    noUndefined: {
      disabled: false,      // set to true to return to original error messages
      attributes: {         // attributes to set for the undefined control sequence
        mathcolor: "red"
      }
    },

    unicode: {
      fonts: "STIXGeneral,'Arial Unicode MS'"  // the default font list for unknown characters
    }

  },

  AsciiMath: {
    displaystyle: true,

    decimal: "."
  },

  MathML: {
    useMathMLspacing: false
  },

  "HTML-CSS": {

    scale: 100,

    minScaleAdjust: 50,

    availableFonts: ["STIX","TeX"],

    preferredFont: "TeX",

    webFont: "TeX",

    imageFont: "TeX",

    undefinedFamily: "STIXGeneral,'Arial Unicode MS',serif",

    mtextFontInherit: false,

    EqnChunk: 50,
    EqnChunkFactor: 1.5,
    EqnChunkDelay: 100,

    linebreaks: {

      automatic: false,

      width: "container"
    },

    styles: {},

    tooltip: {
      delayPost: 600,          // milliseconds delay before tooltip is posted after mouseover
      delayClear: 600,         // milliseconds delay before tooltip is cleared after mouseout
      offsetX: 10, offsetY: 5  // pixels to offset tooltip from mouse position
    }
  },

  NativeMML: {

    scale: 100,

    minScaleAdjust: 50,

    styles: {}
  },

  "SVG": {

    scale: 100,

    minScaleAdjust: 50,

    font: "TeX",

    blacker: 10,

    undefinedFamily: "STIXGeneral,'Arial Unicode MS',serif",

    mtextFontInherit: false,

    addMMLclasses: false,

    EqnChunk: 50,
    EqnChunkFactor: 1.5,
    EqnChunkDelay: 100,

    linebreaks: {

      automatic: false,

      width: "container"
    },

    styles: {},

    tooltip: {
      delayPost: 600,          // milliseconds delay before tooltip is posted after mouseover
      delayClear: 600,         // milliseconds delay before tooltip is cleared after mouseout
      offsetX: 10, offsetY: 5  // pixels to offset tooltip from mouse position
    }
  },

  MathMenu: {
    delay: 150,

    helpURL: "http://www.mathjax.org/help-v2/user/",

    showRenderer: true,
    showMathPlayer: true,
    showFontMenu: false,
    showContext:  false,
    showDiscoverable: false,

    windowSettings: {
      status: "no", toolbar: "no", locationbar: "no", menubar: "no",
      directories: "no", personalbar: "no", resizable: "yes", scrollbars: "yes",
      width: 100, height: 50
    },

    styles: {}

  },

  MathEvents: {
    hover: 500
  },

  MMLorHTML: {
    prefer: {
      MSIE:    "MML",
      Firefox: "HTML",
      Opera:   "HTML",
      Safari:  "HTML",
      Chrome:  "HTML",
      other:   "HTML"
    }
  }
});

</script>