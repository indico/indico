/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

/*
 * HTML Parser By John Resig (ejohn.org) which is based on Erik Arvidsson SimpleHtmlParser
 * extended and modified by Indico Team.
 * Original code by Erik Arvidsson, GPLv2
 * http://erik.eae.net/simplehtmlparser/simplehtmlparser.js
 *
 * // Use like so:
 * HTMLParser(htmlString, {
 *     start: function(tag, attrs, unary) {},
 *     end: function(tag) {},
 *     chars: function(text) {},
 *     comment: function(text) {},
 *     escape: function(text, tag) {}
 * });
 *
 * // or to escape harmful html and scripts
 * escapeHarmfulHTML(htmlString, sanitizationLevel, params);
 *
 * // or to get an XML string:
 * HTMLtoXML(htmlString);
 *
 * // or to get an XML DOM Document
 * HTMLtoDOM(htmlString);
 *
 * // or to inject into an existing document/DOM node
 * HTMLtoDOM(htmlString, document);
 * HTMLtoDOM(htmlString, document.body);
 *
 * //or to parse an inline CSS
 * inlineCSSParser(cssString, params);
 *
 */

// Regular Expressions for parsing tags and attributes
var startTag = /^<[!?]?([^\s<>]+)((?:\s+[\w\-\:\"\.\/]+(?:\s*=\s*(?:(?:"[^"]*")|(?:'[^']*')|[^>\s]+))?)*)\s*(\/?)>/,
        endTag = /^<\/(\w+)[^>]*>/,
        attr = /([\w\-\:\"\.\/]+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:'((?:\\.|[^'])*)')|([^>\s]+)))?/g,
        eMail = /^([a-zA-Z0-9\-_]+.)*[a-zA-Z0-9\-_]+@([a-zA-Z0-9\-_]+.)*[a-zA-Z0-9\-_]+$/;


//Default parameters

// Empty Elements - HTML 4.01
var emptyElements = makeMap("area,base,basefont,br,col,frame,hr,img,input,isindex,link,meta,param,embed");

// Block Elements - HTML 4.01
var block = makeMap("address,applet,blockquote,button,center,dd,del,dir,div,dl,dt,fieldset,form,frameset,hr,iframe,ins,isindex,li,map,menu,noframes,noscript,object,ol,p,pre,table,tbody,td,tfoot,th,thead,tr,ul");

// Inline Elements - HTML 4.01
var inline = makeMap("a,abbr,acronym,applet,b,basefont,bdo,big,br,button,cite,code,del,dfn,em,font,i,iframe,img,input,ins,kbd,label,map,object,q,s,samp,select,small,span,strike,strong,sub,sup,textarea,tt,u,var");

// Elements that you can, intentionally, leave open
// (and which close themselves)
var closeSelf = makeMap("colgroup,dd,dt,li,options,p,td,tfoot,th,thead,tr");

// Attributes that have their values filled in disabled="disabled"
var fillAttrs = makeMap("checked,compact,declare,defer,disabled,ismap,multiple,nohref,noresize,noshade,nowrap,readonly,selected");

var escapeElements = makeMap("script,style,object,applet,embed,form");

// Special Elements (can contain anything)
var special = makeMap("");

type("HTMLParser", [],
        {
            parse: function() {
                var self = this;
                var index, chars, match, last = this.html;

                var parseStartTag = function ( tag, tagName, rest, unary ) {
                    var tagNameLower = tagName.toLowerCase();
                    if ( self.block[ tagNameLower ] ) {
                        while ( self.stack.last() && self.inline[ self.stack.last() ] ) {
                            parseEndTag( "", self.stack.last() );
                        }
                    }

                    if ( self.closeSelf[ tagNameLower ] && self.stack.last() == tagNameLower ) {
                        parseEndTag( "", tagName );
                    }

                    unary = !self.escapeElements[ tagNameLower ] && (self.empty[ tagNameLower ] || !!unary);

                    if ( !unary )
                        self.stack.push( tagName );

                    if ( self.handler.start ) {
                        var attrs = [];

                        rest.replace(attr, function(match, name) {
                            var value = arguments[2] ? arguments[2] :
                                arguments[3] ? arguments[3] :
                                arguments[4] ? arguments[4] :
                                fillAttrs[name] ? name : "";

                            attrs.push({
                                name: name,
                                value: value,
                                escaped: value.replace(/(^|[^\\])"/g, '$1\\\"') //"
                            });
                        });

                        self.handler.start( tagName, attrs, unary );
                    }
                };

                var parseEndTag = function( tag, tagName ) {
                    var tagNameLower = tagName ? tagName.toLowerCase() : undefined;
                    var pos = 0;

                    if ( tagName ) {
                        // Find the closest opened tag of the same type
                        for ( pos = self.stack.length - 1; pos >= 0; pos-- )
                            if ( self.stack[ pos ].toLowerCase() == tagNameLower )
                                break;
                    }

                    if ( pos >= 0 ) {
                        // Close all the open elements, up the stack
                        for ( var i = self.stack.length - 1; i >= pos; i-- )
                            if ( self.handler.end )
                                self.handler.end( self.stack[ i ] );

                        // Remove the open elements from the stack
                        self.stack.length = pos;
                    }
                };

                while ( this.html ) {
                    chars = true;

                    // Make sure we're not in a script or style element
                    if ( !this.stack.last() || (!this.special[ this.stack.last() ] && !this.escapeElements[ this.stack.last() ])) {

                        // Comment
                        if ( this.html.indexOf("<!--") == 0 ) {
                            index = this.html.indexOf("-->");

                            if ( index >= 0 ) {
                                if ( this.handler.comment )
                                    this.handler.comment( this.html.substring( 4, index ) );
                                this.html = this.html.substring( index + 3 );
                                chars = false;
                            }

                        // end tag
                        } else if ( this.html.indexOf("</") == 0 ) {
                            match = this.html.match( endTag );

                            if ( match ) {
                                this.html = this.html.substring( match[0].length );
                                match[0].replace( endTag, parseEndTag );
                                chars = false;
                            }

                        // start tag or 'less than' character
                        } else if ( this.html.indexOf("<") == 0 ) {
                            //checking if '<' is a tag or simple 'less than' char
                            if(this.html.indexOf(">") != -1 &&
                              (this.html.indexOf("<",1) == -1  || this.html.indexOf("<",1) > this.html.indexOf(">"))) {
                                match = this.html.match( startTag );

                                if ( match ) {
                                    this.html = this.html.substring( match[0].length );
                                    match[0].replace( startTag, parseStartTag );
                                    chars = false;
                                }
                            } else {
                                this.html = this.html.substring( 1 );

                                if ( this.handler.chars )
                                    this.handler.chars( "&lt;" );
                            }

                        }

                        if ( chars ) {
                            index = this.html.indexOf("<");

                            var text = index < 0 ? this.html : this.html.substring( 0, index );
                            this.html = index < 0 ? "" : this.html.substring( index );

                            if ( this.handler.chars )
                                this.handler.chars( text );
                        }

                    } else if(!this.escapeElements[ this.stack.last() ]){
                        this.html = this.html.replace(new RegExp("(.*)<\/" + this.stack.last() + "[^>]*>"), function(all, text){
                            text = text.replace(/<!--(.*?)-->/g, "$1")
                                .replace(/<!\[CDATA\[(.*?)]]>/g, "$1");

                            if ( this.handler.chars )
                                this.handler.chars( text );

                            return "";
                        });

                        parseEndTag( "", this.stack.last() );
                    } else {
                        var index = this.html.toLowerCase().indexOf("</" + this.stack.last() + ">");
                        var text = index < 0 ? this.html : this.html.substring( 0, index );
                        this.html = index < 0 ? "" : this.html.substring( index + this.stack.last().length + 3);

                        if( this.handler.escape )
                            this.handler.escape( text , this.stack.last() );
                        this.stack.pop();
                    }

                    if ( this.html == last )
                        throw "Parse Error: " + this.html;
                    last = this.html;
                }

                // Clean up any remaining tags
                parseEndTag();
            }
        /**Core of the parser.
         * @param (string) html Text to be parsed.
         * @param (dictionary) handler Dictionary of functions used to handle particular events.
         *                     handler.start: function(tag, attrs, unary) - called at the beginning of a tag
         *                     handler.end: function(tag) - called during closing a tag
         *                     handler.chars: function(text) - called when parsing through characters between tags
         *                     handler.comment: function(text) - called when parsing comments
         *                     handler.escape: function(text,  tag) - called when parsing text between escaped tags.
         * @param (dictionary) params Parser parameters. If not set defaults are used. See them at the beginning of the type.
         *                     params.empty - list of elements that don't need to be closed
         *                     params.block - list of block elements
         *                     params.inline - list of inline elements
         *                     params.closeSelf - list of elements which are closing themselves
         *                     params.fillAttrs - list of attributes which can be filled by default value.
         *                     params.escapeElements - list of tags between which text is escaped
         *                     params.special - list of tags between text remains unchanged
         */
        },
        function( html, handler, params ) {
            this.html = html;
            this.handler = handler;
            this.stack = [];
            this.stack.last = function(){
                return this[ this.length - 1 ];
            };

            this.empty = params && params.empty ? params.empty : emptyElements;
            this.block = params && params.block ? params.block : block;
            this.inline = params && params.inline ? params.inline : inline;
            this.closeSelf = params && params.closeSelf ? params.closeSelf : closeSelf;
            this.fillAttrs = params && params.fillAttrs ? params.fillAttrs : fillAttrs;
            this.escapeElements = params && params.escapeElements ? params.escapeElements : escapeElements;
            this.special = params && params.special ? params.special : special;
        });

//Default parameters

//Properties which can appear in a CSS
var propertyWhitelist = makeMap( Indico.Security.allowedCssProperties );

type("inlineCSSParser",[],
        {
            parse: function(){
                var result = "";
                var security = 0;
                var errorList = [];

                // disallow urls
                this.css = this.css.replace(/url\s*\(\s*[^\s)]+?\s*\)\s*/, ' ');
                // gauntlet
                if (!(/^([\-:,;#%.\sa-zA-Z0-9!]|\w-\w|'[\s\w]+'|"[\s\w]+"|\([\d,\s]+\))*$/).test(this.css))
                    throw "Parse Error: " + this.css;
                if (!(/^\s*([-\w]+\s*:[^:;]*(;\s*|$))*$/).test(this.css))
                    throw "Parse Error: " + this.css;

                var parts = this.css.split(/;/g);
                for(var i in parts)
                    if( parts[i].replace(/\s/g,'') != ""){
                        var property = parts[i].split(/:/g)[0].replace(/\s/g,'');
                        var values = parts[i].split(/:/g)[1].split(/\s/g);
                        var value = "";
                        for(var j in values)
                            value += " " + values[j].replace(/\s/g,'')
                        if (this.propertyWhitelist[property.toLowerCase()] && value)
                            result += property + ':' + value + ';';
                        else{
                            security = 1;
                            errorList.push(property)
                        }
                    }
                return [result, security, errorList];
            }
        },
        /**Cleans text from not proper css properties and values.
         * @param (String) css Text to be parsed.
         * @param (dictionary) params Parser parameters. If not set defaults are used. Take a look at the beginning of the type.
         *                            params.propertyWhitelist - accepted list of properties.
         * @returns (tuple(string, security)) First element of the tuple is parsed text. Second one indicates which actions was done during parsing:
         *                                    0 - removing not necessary whitespace or empty values.
         *                                    1 - removing potentially dangerous values and properties.
         **/
        function(css, params){
            this.css = css;
            this.propertyWhitelist = params && params.propertyWhitelist ? params.propertyWhitelist : propertyWhitelist;
        });


var defaultTagWhitelist = makeMap( Indico.Security.allowedTags );

var defaultAttribWhitelist = makeMap( Indico.Security.allowedAttributes );

var defaultAllowedProtocols = makeMap( Indico.Security.allowedProtocols );

var urlProperties = makeMap(Indico.Security.urlProperties);

/**Cleans text from scripts, styles and potentialy harmful html.
 * @param (String) html Text to be parsed.
  * @param sanitizationLevel Current indico sanitization level. If 0 or 3 text is not parsed at all. If 1 inline css script are deleted. If 2 text is parsed normally.
 * @param (dictionary) params Parser parameters. For further description see 'params' in HTMLParser and inlineCSSParser types.
 *                     params.tagWhitelist String containing tags to be accepted by parser in lowercase separated by coma(without whitespace). If not defined defualts is used.
 *                     params.attribWhitelist String containing attributes to be accepted by parser in lowercase separated by coma(without whitespace). If not defined defualts is used.
 *                     params.allowedProtocols String contains allowed protocols.
 *                     params.strict If true while parsing style fails exception is thrown. False by default.
 * @returns (tuple(string, security)) First element of the tuple is parsed text. Second one indicates which actions was done during parsing:
 *                                    0 - removing empty attibutes, closing not closed tags, removing whitespace.
 *                                    1 - removing potentially dangerous HTML tags and attributes.
 *                                    2 - removing scripts, objects, applets, embed etc.
 **/
function escapeHarmfulHTML( html, sanitizationLevel, params ) {

    sanitizationLevel = sanitizationLevel == undefined ? Indico.Security.sanitizationLevel : sanitizationLevel;

    if( sanitizationLevel == 1 || sanitizationLevel == 2  )
    {
        var self = this;
        var strict = params && params.strict || false;

        //Result string
        var results = "";

        //Tags which can occur in the string. Other tags are omitted.
        var tagWhitelist = params && params.tagWhitelist ? params.tagWhitelist : defaultTagWhitelist;

        //Attributes allowed.
        var attribWhitelist = params && params.attribWhitelist ? params.attribWhitelist : defaultAttribWhitelist;

        //Protocols allowed
        var allowedProtocols = params && params.allowedProtocols ? params.allowedProtocols : defaultAllowedProtocols;

        var urlRegexpStr = "^(";
        for (var protocol in allowedProtocols)
            urlRegexpStr += "|" + protocol;
        urlRegexpStr += ")://[^<>.][^<>]*$";
        var urlRegexp = new RegExp(urlRegexpStr);

        function isEmail(value) {
            return eMail.test(value);
        }

        function isUrl(value) {
            return urlRegexp.test(value);
        }

        var security = 0;

        var errorList = [];

        var parser = new HTMLParser(html, {
            start: function( tag, attrs, unary ) {
            if( tagWhitelist[tag.toLowerCase()] ) {
                results += "<" + tag;

                for ( var i = 0; i < attrs.length; i++ )
                    if(attrs[i].name.toLowerCase() == "style" && sanitizationLevel == 2) {
                        try{
                            var cssParser = new inlineCSSParser(attrs[i].escaped, params);
                            var tuple = cssParser.parse();
                        }
                        catch(error){
                            if(typeof error == "string" && error.indexOf("Parse Error") != -1 && !strict)
                                var tuple = ["",1];
                            else
                                throw error;
                        }
                        if(tuple[0] != '')
                            results += " " + attrs[i].name + '="' + tuple[0] + '"';
                        security = max(security, tuple[1]);
                        errorList = errorList.concat(tuple[2])
                    }
                    else if(attribWhitelist[ attrs[i].name.toLowerCase() ] || unary && attrs[i].name == '/') {
                        if(urlProperties[attrs[i].name.toLowerCase()]){
                            attrs[i].escaped = attrs[i].escaped.replace(/[`\000-\040\177-\240\s]+/g, '');
                            attrs[i].escaped = attrs[i].escaped.replace(/\ufffd/g, "");
                            if (/^[a-z0-9][-+.a-z0-9]*:/.test(attrs[i].escaped) && !allowedProtocols[attrs[i].escaped.split(':')[0].toLowerCase()]) {
                                security = 1;
                                errorList.push(attrs[i].escaped);
                                continue;
                            }
                        }
                        if( attrs[i].escaped != '')
                            results += " " + attrs[i].name + '="' + attrs[i].escaped + '"';
                    }
                    else{
                        security = max(security, 1);
                        errorList.push(attrs[i].name);
                    }

                results += (unary ? " /" : "") + ">";
            }
            else if(isEmail(tag) || isUrl(tag)) {
                results += "<" + tag + ">";
            }
            else {
                security = max(1, security);
                errorList.push(tag);
            }
        },
        end: function( tag ) {
            if(tagWhitelist[tag.toLowerCase()])
                results += "</" + tag + ">";
            else if(isEmail(tag) || isUrl(tag))
                return;
            else{
                security = max(1, security);
            }
        },
        chars: function( text ) {
            results += text;
        },
        comment: function( text ) {
           // results += "<!--" + text + "-->";
        },
        escape: function(text, tag) {
            security = max(2, security);
            errorList.push(tag);
        }
        }, params);

        parser.parse();

        return [results, security,errorList];
    }
    else
        return [html,0,[]];
};

function HTMLtoXML( html ) {
    var results = "";

    var parser = new HTMLParser(html, {
        start: function( tag, attrs, unary ) {
        results += "<" + tag;

        for ( var i = 0; i < attrs.length; i++ )
            results += " " + attrs[i].name + '="' + attrs[i].escaped + '"';

        results += (unary ? "/" : "") + ">";
    },
    end: function( tag ) {
        results += "</" + tag + ">";
    },
    chars: function( text ) {
        results += text;
    },
    comment: function( text ) {
        results += "<!--" + text + "-->";
    }
    });

    parser.parse();

    return results;
};

function HTMLtoDOM( html, doc ) {
    // There can be only one of these elements
    var one = makeMap("html,head,body,title");

    // Enforce a structure for the document
    var structure = {
            link: "head",
            base: "head"
    };

    if ( !doc ) {
        if ( typeof DOMDocument != "undefined" )
            doc = new DOMDocument();
        else if ( typeof document != "undefined" && document.implementation && document.implementation.createDocument )
            doc = document.implementation.createDocument("", "", null);
        else if ( typeof ActiveX != "undefined" )
            doc = new ActiveXObject("Msxml.DOMDocument");

    } else
        doc = doc.ownerDocument ||
        doc.getOwnerDocument && doc.getOwnerDocument() ||
        doc;

    var elems = [],
    documentElement = doc.documentElement ||
    doc.getDocumentElement && doc.getDocumentElement();

    // If we're dealing with an empty document then we
    // need to pre-populate it with the HTML document structure
    if ( !documentElement && doc.createElement ) (function(){
        var html = doc.createElement("html");
        var head = doc.createElement("head");
        head.appendChild( doc.createElement("title") );
        html.appendChild( head );
        html.appendChild( doc.createElement("body") );
        doc.appendChild( html );
    })();

    // Find all the unique elements
    if ( doc.getElementsByTagName )
        for ( var i in one )
            one[ i ] = doc.getElementsByTagName( i )[0];

    // If we're working with a document, inject contents into
    // the body element
    var curParentNode = one.body;

    var parser = new HTMLParser( html, {
        start: function( tagName, attrs, unary ) {
        // If it's a pre-built element, then we can ignore
        // its construction
        if ( one[ tagName ] ) {
            curParentNode = one[ tagName ];
            return;
        }

        var elem = doc.createElement( tagName );

        for ( var attr in attrs )
            elem.setAttribute( attrs[ attr ].name, attrs[ attr ].value );

        if ( structure[ tagName ] && typeof one[ structure[ tagName ] ] != "boolean" )
            one[ structure[ tagName ] ].appendChild( elem );

        else if ( curParentNode && curParentNode.appendChild )
            curParentNode.appendChild( elem );

        if ( !unary ) {
            elems.push( elem );
            curParentNode = elem;
        }
    },
    end: function( tag ) {
        elems.length -= 1;

        // Init the new parentNode
        curParentNode = elems[ elems.length - 1 ];
    },
    chars: function( text ) {
        curParentNode.appendChild( doc.createTextNode( text ) );
    },
    comment: function( text ) {
        // create comment node
    }
    });

    parser.parse();

    return doc;
};

function makeMap(str){
    var obj = {}, items = str.split(",");
    for ( var i = 0; i < items.length; i++ )
        obj[ items[i] ] = true;
    return obj;
};

function max(val1, val2){
    return val1 > val2 ? val1 : val2;
};
