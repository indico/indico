var Json = {
    /**
     * Encodes the object into a json.
     * @param {Object} object
     * @return {String} json
     */
    write: function(object) {
        if (!exists(object)) {
            return "null";
        }
        switch (typeof(object)) {
            case "boolean":
            case "number":
                return str(object);
            case "string":
                return escapeString(object);
            case "object":
                if (object.Getter) {
                    return Json.write(object.get());
                }
                if (object.Dictionary) {
                    object = object.getAll();
                }
                if (object.Enumerable) {
                    return "[" + object.each(stacker(Json.write)).join(",") + "]";
                }
                if (isArray(object)) {
                    return "[" + iterate(object, stacker(Json.write)).join(",") + "]";
                }
                var properties = [];
                enumerate(object, function(value, key) {
                    if (!isFunction(value)) {
                        properties.push(escapeString(key) + ":" + Json.write(value));
                    }
                });
                return "{" + properties.join(",") + "}";
            default:
                throw "Invalid object: " + str(object);
        }
    }
};
