var ScriptRoot = "../";

function include(script) {
    jstestdriver.console.log("include called");
    document.write("<script type=\"text/javascript\" src=\"" + script + "\"></script>");
}

var Indico = {
        Urls: {
            SecureImagesBase: "URLSecureImagesBase",
            SecureJsonRpcService: "URLSecureJsonRpcService",
            JsonRpcService: "URLJsonRpcService",
            ImagesBase: "URLImagesBase"
            },
        SystemIcons: {
            conference: "ICONconference",
            lecture: "ICONlecture",
            meeting: "ICONmeeting",
            }
};
