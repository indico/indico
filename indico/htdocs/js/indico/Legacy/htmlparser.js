/*
 * HTML Parser By John Resig (ejohn.org)
 * Original code by Erik Arvidsson, Mozilla Public License
 * http://erik.eae.net/simplehtmlparser/simplehtmlparser.js
 *
 * // Use like so:
 * HTMLParser(htmlString, {
 *     start: function(tag, attrs, unary) {},
 *     end: function(tag) {},
 *     chars: function(text) {},
 *     comment: function(text) {}
 * });
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
 */

(function(){

    // Regular Expressions for parsing tags and attributes
    var startTag = /^<(\w+)((?:\s+\w+(?:\s*=\s*(?:(?:"[^"]*")|(?:'[^']*')|[^>\s]+))?)*)\s*(\/?)>/,
        endTag = /^<\/(\w+)[^>]*>/,
        attr = /(\w+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:'((?:\\.|[^'])*)')|([^>\s]+)))?/g;

    // Empty Elements - HTML 4.01
    var empty = makeMap("area,base,basefont,br,col,frame,hr,img,input,isindex,link,meta,param,embed");

    // Block Elements - HTML 4.01
    var block = makeMap("address,applet,blockquote,button,center,dd,del,dir,div,dl,dt,fieldset,form,frameset,hr,iframe,ins,isindex,li,map,menu,noframes,noscript,object,ol,p,pre,table,tbody,td,tfoot,th,thead,tr,ul");

    // Inline Elements - HTML 4.01
    var inline = makeMap("a,abbr,acronym,applet,b,basefont,bdo,big,br,button,cite,code,del,dfn,em,font,i,iframe,img,input,ins,kbd,label,map,object,q,s,samp,select,small,span,strike,strong,sub,sup,textarea,tt,u,var");

    // Elements that you can, intentionally, leave open
    // (and which close themselves)
    var closeSelf = makeMap("colgroup,dd,dt,li,options,p,td,tfoot,th,thead,tr");

    // Attributes that have their values filled in disabled="disabled"
    var fillAttrs = makeMap("checked,compact,declare,defer,disabled,ismap,multiple,nohref,noresize,noshade,nowrap,readonly,selected");

    // Special Elements (can contain anything)
    var special = makeMap("");

    var HTMLParser = this.HTMLParser = function( html, handler ) {
        var index, chars, match, stack = [], last = html;
        stack.last = function(){
            return this[ this.length - 1 ];
        };

        while ( html ) {
            chars = true;

            // Make sure we're not in a script or style element
            if ( !stack.last() || !special[ stack.last() ] ) {

                // Comment
                if ( html.indexOf("<!--") == 0 ) {
                    index = html.indexOf("-->");

                    if ( index >= 0 ) {
                        if ( handler.comment )
                            handler.comment( html.substring( 4, index ) );
                        html = html.substring( index + 3 );
                        chars = false;
                    }

                // end tag
                } else if ( html.indexOf("</") == 0 ) {
                    match = html.match( endTag );

                    if ( match ) {
                        html = html.substring( match[0].length );
                        match[0].replace( endTag, parseEndTag );
                        chars = false;
                    }

                // start tag
                } else if ( html.indexOf("<") == 0 ) {
                    match = html.match( startTag );

                    if ( match ) {
                        html = html.substring( match[0].length );
                        match[0].replace( startTag, parseStartTag );
                        chars = false;
                    }
                }

                if ( chars ) {
                    index = html.indexOf("<");

                    var text = index < 0 ? html : html.substring( 0, index );
                    html = index < 0 ? "" : html.substring( index );

                    if ( handler.chars )
                        handler.chars( text );
                }

            } else {
                html = html.replace(new RegExp("(.*)<\/" + stack.last() + "[^>]*>"), function(all, text){
                    text = text.replace(/<!--(.*?)-->/g, "$1")
                        .replace(/<!\[CDATA\[(.*?)]]>/g, "$1");

                    if ( handler.chars )
                        handler.chars( text );

                    return "";
                });

                parseEndTag( "", stack.last() );
            }

            if ( html == last )
                throw "Parse Error: " + html;
            last = html;
        }

        // Clean up any remaining tags
        parseEndTag();

        function parseStartTag( tag, tagName, rest, unary ) {
            tag = tag.toLowerCase();
            tagName = tagName.toLowerCase();

            if ( block[ tagName ] ) {
                while ( stack.last() && inline[ stack.last() ] ) {
                    parseEndTag( "", stack.last() );
                }
            }

            if ( closeSelf[ tagName ] && stack.last() == tagName ) {
                parseEndTag( "", tagName );
            }

            unary = empty[ tagName ] || !!unary;

            if ( !unary )
                stack.push( tagName );

            if ( handler.start ) {
                var attrs = [];

                rest.replace(attr, function(match, name) {
                    var value = arguments[2] ? arguments[2] :
                        arguments[3] ? arguments[3] :
                        arguments[4] ? arguments[4] :
                        fillAttrs[name] ? name : "";

                    attrs.push({
                        name: name.toLowerCase(),
                        value: value.toLowerCase(),
                        escaped: value.replace(/(^|[^\\])"/g, '$1\\\"').toLowerCase() //"
                    });
                });

                if ( handler.start )
                    handler.start( tagName, attrs, unary );
            }
        }

        function parseEndTag( tag, tagName ) {
            if(tag)
                tag = tag.toLowerCase();
            if(tagName)
                tagName = tagName.toLowerCase();

            // If no tag name is provided, clean shop
            if ( !tagName )
                var pos = 0;

            // Find the closest opened tag of the same type
            else
                for ( var pos = stack.length - 1; pos >= 0; pos-- )
                    if ( stack[ pos ] == tagName )
                        break;

            if ( pos >= 0 ) {
                // Close all the open elements, up the stack
                for ( var i = stack.length - 1; i >= pos; i-- )
                    if ( handler.end )
                        handler.end( stack[ i ] );

                // Remove the open elements from the stack
                stack.length = pos;
            }
        }
    };

    /**Cleans text from not proper css properties and values.
      * @param (String) css Text to be parsed.
      * @returns (tuple(string, security)) First element of the tuple is parsed text. Second one indicates which actions was done during parsing:
      *                                    0 - removing removing not necessary whitespace or empty values.
      *                                    1 - removing potentially dangerous values and properties.
      **/
    this.inlineCSSParser = function(css)
    {

        // Regular Expressions for parsing properties and values
        var propertyPattern = /(\s*)[\w-]+(\s*):/;
        var valueElement = /(\s*)(\w+)[\s)(,*]/;
        var valuePattern = /((\s*)[\w)(,]+(\s*))+;/;

        //Properties which can appear in a CSS
        var propertyWhitelist = makeMap("background-color,font-size,font-family,font-style,font,font-variant,font-weigth," +
                                        "text-align,margin,margin-left,margin-rigth,margin-top,margin-bottom,color");

        //Values which cannot appear in a CSS
        var valueBlacklist = makeMap("");

        //
        var result = "";
        var property;
        var values;
        var security = 0;

        while (css.replace(/\s+/g,"")){

            property = getProperty();
            values = getValues();

            if(propertyWhitelist[property])
            {
                result += property + ":";
                for(var i = 0; i < values.length; ++i)
                    if(!valueBlacklist[values[i]])
                        result += " " + values[i];
                    else
                        security = 1;
                result += ";";
            }
            else
                security = 1;
        }

        return [result, security];

        function getProperty(){
            var property = css.match(propertyPattern);
            if(property){
                css = css.substring(property[0].length);
                return property[0].substring(0, property[0].length - 1).replace(/\s+/g,"");
            }
            throw "Parse Error: " + css;
        };

        function getValues(){
            var values = css.match(valuePattern);
            var valuesTable = [];
            var tmp;
            if(values) {
                css = css.substring(values[0].length);
                while(values[0] != ";"){
                    tmp = values[0].match(valueElement);
                    values[0] = values[0].substring(tmp[0].length);
                    valuesTable.push(tmp[0].replace(/\s+/g,""));
                }
                return valuesTable;

            }
            throw "Parse Error: " + css;
        };

    };

    /**Cleans text from scripts, styles and potentialy harmful html.
      * @param (String) html Text to be parsed.
      * @param (String) tags String containing tags to be accepted by parser in lowercase separated by coma(without whitespace). If not defined defualts is used.
      * @param (String) attrs String containing attributes to be accepted by parser in lowercase separated by coma(without whitespace). If not defined defualts is used.
      * @param (String) escape String containing between which text is erased in lowercase separated by coma(without whitespace). If not defined defualts is used.
      * @param (Boolean) strict If true while parsing style fails exception is thrown. False by default.
      * @returns (tuple(string, security)) First element of the tuple is parsed text. Second one indicates which actions was done during parsing:
      *                                    0 - removing empty attibutes, closing not closed tags, removing whitespace.
      *                                    1 - removing potentially dangerous HTML tags and attributes.
      *                                    2 - removing scripts, objects, applets, embed etc.
      **/
    this.escapeHarmfulHTML = function( html, tags, attrs, escape, strict ) {

        strict = strict || false;

        //Result string
        var results = "";

        //Tags which can occur in the string. Other tags are omitted.
        var tagWhitelist = tags ? makeMap(tags) : makeMap("a,p,br,blockquote,strong,b,u,i,em,ul,ol,li,span,sub,sup,div,pre,address");

        //Attributes allowed.
        var attribWhitelist = attrs ? makeMap(attrs) : makeMap("href,name,class,style");

        //Tags between which all text is erased.
        var escapeElements = escape ? makeMap(escape) : makeMap("script,style,object,applet,embed,form");

        //Variable to count nested escapeElements.
        var ignoreText = 0;

        var security = 0;

        HTMLParser(html, {
            start: function( tag, attrs, unary ) {
                if( escapeElements[tag] ){
                    security = 2;
                    ++ignoreText;
                }
                else if( tagWhitelist[tag] && ignoreText == 0) {
                    results += "<" + tag;

                    for ( var i = 0; i < attrs.length; i++ )
                        if(attribWhitelist[ attrs[i].name ] ) {
                            if(attrs[i].name == "style") {
                                try{
                                    var tuple = inlineCSSParser(attrs[i].escaped);
                                }
                                catch(error){
                                    if(typeof error == "string" && error.indexOf("Parse Error") != -1 && !strict)
                                        var tuple = ["",-1];
                                    else
                                        throw error;
                                }
                                attrs[i].escaped = tuple[0];
                                security = max(security, tuple[1]);
                            }
                            if(attrs[i].escaped)
                                results += " " + attrs[i].name + '="' + attrs[i].escaped + '"';
                        }

                    results += (unary ? "/" : "") + ">";
                }
                else
                    security = max(1, security);
            },
            end: function( tag ) {
                if( escapeElements[tag] && ignoreText > 0)
                    --ignoreText;
                else if(tagWhitelist[tag] && ignoreText == 0)
                {
                    results += "</" + tag + ">";
                }
            },
            chars: function( text ) {
                if( ignoreText == 0 )
                    results += text;
            },
            comment: function( text ) {
                if( ignoreText == 0)
                    results += "<!--" + text + "-->";
            }
        });

        return [results, security];
    };

    this.HTMLtoXML = function( html ) {
        var results = "";

        HTMLParser(html, {
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

        return results;
    };

    this.HTMLtoDOM = function( html, doc ) {
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

        HTMLParser( html, {
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
})();
