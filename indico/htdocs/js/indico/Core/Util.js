/**
 * Calls a URL with a POST request, by building and submitting a hidden form
 * @param {String} url The base url
 * @param {dictionary} getArguments A dictionary with the GET arguments, will be added to the base URL
 *                                  After adding the GET parameters we will call 'encodeURI' on the url
 *                                  This function does not handle values such as lists, etc.
 * @param {dictionary} postArgument A dictionary with the POST arguments.
 *                                  For each argument we will create a hidden field.
 * @param {String} method "post" or "get". "post" by defauly
 * @param {String} separator The separator for the GET arguments in the URL, "&" by default.
 */
Util.postRequest = function(url, getArguments, postArguments, method, separator) {

    method = any(method, "post");
    separator = any(separator, "&");

    var getUrl = url;

    if (exists(getArguments)) {
        first = true;
        each(getArguments, function(value, key) {
            if(first) {
                getUrl += "?";
                first = false;
            } else {
                getUrl += separator;
            }
            getUrl += key + "=" + value;
        });
    }

    var form = Html.form({method: method, action: encodeURI(getUrl)});

    each(postArguments, function(value, key){
        var hiddenField = Html.input("hidden", {name: key});
        hiddenField.dom.value = value;
        form.append(hiddenField);
    });

    $E(document.body).append(form);

    form.dom.submit();
};
