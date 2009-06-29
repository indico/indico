/**
 * Text
 * @author Tom
 */

var dictionaries = {};

/**
 * Loads dictionary for given language
 * @param {String} language
 */
function loadDictionary(language) {
        include(languageDictionaryPath + language + ".js");
}

var defaultLanguage = "en_US";
var languageDictionaryPath = TextRoot;

loadDictionary(defaultLanguage);

/**
 * Returns template for given key and language
 * @param {String} key
 * @param {String} language
 * @return {Function} template
 */
function getTemplate(key, language) {
        if (exists(language)) {
                var dictionary = dictionaries[language];
                if (exists(dictionary)) {
                        var template = dictionary[key];
                        if (exists(template)) {
                                if (!isFunction(template)) {
                                        template = textTemplate(template);
                                        dictionary[key] = template;
                                }
                        }
                        return template;
                } else {
                        return null;
                }
        } else {
                return getTemplate(key, defaultLanguage);
        }
}

var currentLanguage = null;

/**
 * Returns text from template for given key and params
 * @param {String} key
 * @param {String} ... params
 * @return {String} text
 */
function $T(key) {
        var template = getTemplate(key, currentLanguage);
        if (exists(template)) {
                return template($A(arguments, 1));
        } else {
                return key;
        }
}


