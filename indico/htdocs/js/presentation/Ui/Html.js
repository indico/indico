/**
 * Html
 * @author Tom
 */

type("Html", ["XElement", "WatchAccessor", "CanGet"], {
        isField: function() {
                return exists(Html.isCheckField(this.dom));
        },

        isCheckField: function() {
                return Html.isCheckField(this.dom);
        },

        // XElement
        getters: merge(XElement.prototype.getters),
        setters: merge(XElement.prototype.setters),

        styleGetters: merge(XElement.prototype.styleGetters),
        styleSetters: merge(XElement.prototype.styleSetters),

        /**
         * @see XElement.getStyle
         */
        getStyleBase: XElement.prototype.getStyle,
        getStyle: function(key) {
                var value = this.getStyleBase(key);
                return value == "auto" ? null : value;
        },

        // WatchAccessor
        get: function() {
                var checkField = Html.isCheckField(this.dom);
                if (!exists(checkField)) {
                        return Dom.Content.get(this.dom);
                } else if (checkField) {
                        return this.dom.checked;
                } else {
                        return this.dom.value;
                }
        },
        /**
         * Sets value
         * @param {Object} value
         * @param {Object} ... content
         */
        set: function(value) {
                var checkField = Html.isCheckField(this.dom);
                if (!exists(checkField)) {
                        return Dom.Content.set(this.dom, $A(arguments));
                } else if (checkField) {
                        var checked = this.dom.checked;
                        if (checked == !value) {
                                this.dom.checked = !checked;
                                if (exists(this.observers)) {
                                        this.observers(!checked);
                                }
                        }
                } else {
                        this.dom.value = str(value);
                }
        },
        observe: function(observer) {
                var checkField = Html.isCheckField(this.dom);
                if (!exists(checkField)) {
                        return;
                } else {
                        var self = this;
                        var notify = function(evt) {
                            observer(self.get());
                        };
                        if (!exists(this.observers)) {
                                this.observers = commands();
                                var notify = function(evt) {
                                    self.observers(self.get());
                                };
                                if (checkField) {
                                        this.observeClick(notify);
                                } else {
                                        this.observeChange(notify);
                                }
                        }
                        return this.observers.attach(observer);
                }
        },
        invokeObserver: function(observer) {
                return observer(this.get());
        },
        notifyObservers: function() {
                if (this.observers) {
                        this.invokeObserver(this.observers);
                }
        },

        // CanGet
        canGet: function() {
                return this.isField();
        }
},
        function(source, attributes) {
                this.XElement(source, attributes, $A(arguments, 2));
        }
);



extend(Html, {
        toDimensions: function(value) {
                return isNumber(value) ? Math.round(value) + "px" : value;
        },

        isCheckField: function(dom) {
                switch (dom.tagName.toLowerCase()) {
                        case "input":
                                switch (dom.type.toLowerCase()) {
                                        case "checkbox":
                                        case "radio":
                                                return true;
                                        default:
                                                return false;
                                }
                        case "select":
                        case "textarea":
                                return false;
                        default:
                                return null;
                }
        },

        /**
         * Makes attributes from class name or object
         * @param {String, Object} source
         * @param {Object} [other]
         * @return {Object} attributes
         */
        makeAttributes: function(source, other) {
                var attribs;
                if (exists(source)) {
                        attribs = isString(source) ? {
                                className: source
                        } : source;
                        if (exists(other)) {
                                extend(attribs, other);
                        }
                } else {
                        attribs = exists(other) ? other : {};
                }
                for (var key in attribs) {
                        if (attribs[key] === undefined) {
                                        delete attribs[key];
                        }
                }
                return attribs;
        },

        /**
         * Builds an H element with the level, the content, and the attributes.
         * @param {Number} level
         * @param {Object} content
         * @param {String, Object} [attributes]
         * @return {XElement} element
         */
        h: function(level, content, attributes) {
                return new Html("h" + level, Html.makeAttributes(attributes), content);
        },

        /**
         * Builds an INPUT element with the type, the attributes, and the value.
         * @param {String} type
         * @param {Object} [attributes]
         * @param {String} [value]
         * @return {XElement} element
         */
        input: function(type, attributes, value) {
                return new Html("input", Html.makeAttributes(attributes, {
                        type: type,
                        value: value
                }));
        },

        /**
         * Builds an INPUT type=text element with the attributes and the value.
         * @param {Object} [attributes]
         * @param {Object} [value]
         * @return {XElement} element
         */
        edit: function(attributes, value) {
                return new Html("input", Html.makeAttributes(attributes, {
                        type: "text",
                        value: value
                }));
        },

        /**
         * Builds an INPUT type=checkbox element with the attributes and the value.
         * @param {Object} [attributes]
         * @param {Boolean} [checked]
         * @return {XElement} element
         */
        checkbox: function(attributes, checked) {
            var elem = new Html("input", Html.makeAttributes(attributes, {
                type: "checkbox"
            }));

            elem.set(checked);
            return elem;

        },

        /**
         * Builds an INPUT type=radio element with the attributes and the value.
         * @param {Object} [attributes]
         * @param {Boolean} [checked]
         * @return {XElement} element
         */
        radio: function(attributes, checked) {
                return new Html("input", Html.makeAttributes(attributes, {
                        type: "radio",
                        checked: checked
                }));
        },

        email: function(attributes) {
                return new Html("input", Html.makeAttributes(attributes, {
                        type: "text",
                        vcard_name: "vCard.Email"
                }));
        },

        password: function(attributes) {
                return new Html("input", Html.makeAttributes(attributes, {
                        type: "password",
                        autocomplete: "on"
                }));
        },

        hidden: function(attributes) {
                return new Html("div", Html.makeAttributes(attributes)).style({
                        display: "none"
                });
        }
});

iterate([
        /* links */ "a",
        /* boxes */ "div", "span", "p",
        /* lists */ "ul", "ol", "li",
        /* tables */ "table", "caption", "thead", "tfoot", "tbody", "tr", "th", "td",
        /* styles */ "strong", "em", "emp", "pre", "small",
        /* headers */ "h1", "h2", "h3", "h4", "h5", "h6",
        /* controls */ "form", "button", "label", "textarea", "img", "select", "option", "optgroup",
        /* specials */ "object", "param", "embed", "iframe", "br"
], function(tag) {
        Html[tag] = function(attributes) {
                return new Html(tag, Html.makeAttributes(attributes), $A(arguments, 1));
        };
});

Html.prototype.getters.enctype = function() {
        return this.dom.enctype;
};
Html.prototype.setters.enctype = function(value) {
        this.dom.enctype = value;
        if ("encoding" in this.dom) {
                // FIX IE
                this.dom.encoding = value;
        }
        return this.dom;
};

// due to setAttributeNS for Dom.set()
iterate([
        "className", "htmlFor"
], function(name) {
	Html.prototype.getters[name] = function() {
		return this.dom[name];
	};
	Html.prototype.setters[name] = function(value) {
		this.dom[name] = value;
	};
});

delayedBind(Html.prototype.styleGetters, "opacity", function(dom) {
        return Dom.Style.get(dom, "opacity") === undefined
                ? function(dom) {
                        var filter = dom.filters["opacity"];
                        return exists(filter) ? (filter.opacity / 100) : 1;
                }
                : function(dom) {
                        var value = Dom.Style.get(dom, "opacity");
                        return exists(value) ? parseFloat(value) : 1;
                }
});
delayedBind(Html.prototype.styleSetters, "opacity", function() {
        return Browser.IE
                ? function(value) {
                        return objectize("filter", (value == 1 || value === "") ? ""
                                : ("progid:DXImageTransform.Microsoft.Alpha(opacity=" + Math.round(((value < 0.00001) ? 0 : value) * 100) + ")"));
                }
                : function(value) {
                        return objectize("opacity", (value == 1 || value === "") ? "" : (value < 0.00001) ? 0 : value);
                }
});

delayedBind(Html.prototype.styleGetters, "cssFloat", function(dom) {
        return Dom.Style.get(dom, "cssFloat") === undefined
                ? function(dom) {
                        return Dom.Style.get(dom, "styleFloat");
                }
                : function(dom) {
                        return Dom.Style.get(dom, "cssFloat");
                }
});
delayedBind(Html.prototype.styleSetters, "cssFloat", function() {
        return Browser.IE
                ? function(value) {
                        return objectize("styleFloat", Html.toDimensions(value));
                }
                : function(value) {
                        return objectize("cssFloat", Html.toDimensions(value));
                }
});

iterate([
        "left", "right", "top", "bottom", "width", "height", "borderWidth",
        "padding", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
        "margin", "marginTop", "marginRight", "marginBottom", "marginLeft",
        "border", "borderTop", "borderRight", "borderBottom", "borderLeft",
        "lineHeight"
], function(key) {
        Html.prototype.styleSetters[key] = function(value) {
                return objectize(key, Html.toDimensions(value));
        };
});

iterate([
        "margin", "padding", "border"
], function(name) {
        iterate([
                "Top", "Right", "Bottom", "Left"
        ], function(dir) {
                var key = name + dir;
                Html.prototype.styleSetters[key] = function(value) {
                        return objectize(key, Html.toDimensions(value));
                };
        });

        Html.prototype.styleSetters[name] = function(value) {
                if (isObject(value)) {
                        var obj = {};
                        iterate([
                                "Top", "Right", "Bottom", "Left"
                        ], function(dir) {
                                var key = dir.toLowerCase();
                                if (key in value) {
                                        obj[name + dir] = value[key];
                                }
                        });
                        return obj;
                } else {
                        return objectize(name, Html.toDimensions(value));
                }
        };
});


iterate([
        "selected", "disabled"
], function(name) {
        Html.prototype.getters[name] = function() {
                return exists(Dom.get(this.dom, name));
        };
        Html.prototype.setters[name] = function(value) {
                return Dom.set(this.dom, name, value ? name : null);
        };
});


/**
 * Generates a new id for HTML element.
 * @return {String}
 */
Html.generateId = function() {
        return "_GID" + Html.generateId.current++;
};
Html.generateId.current = 1;

Html.addScript = function(path) {
        var script = document.createElement("script");
        script.src = path;
        script.type = "text/javascript";
        document.getElementsByTagName("head")[0].appendChild(script);
};

Html.Target = {
        New: "_blank"
};

Html.$ = function() {
    return new XElement($.apply(this, arguments).get(0));
};
