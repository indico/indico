<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
            "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <title>Indico</title>
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <link href="${ Config.getInstance().getSystemIconURL("addressBarIcon") }" type="image/x-icon" rel="shortcut icon" />

        <style type="text/css">
            body {
                background:none repeat scroll 0 0 #FFFFFF;
                font-family: arial,serif;
                font-size: 14px;
                margin: 0;
                padding: 0;
                line-height: 18pt;
            }
            a:link, a:visited {
                color: #0B63A5;
                text-decoration: none;
            }
            a:hover {
                color: #E25300;
            }
            img.headerLogo {
                border: medium none;
                height: 52px;
                margin: 7px 10px;
                width: 196px;
            }
            #errorBoxContainer h1 {
                color: #777777;
                font-size: 20px;
                padding-bottom: 10px;
            }
            .leftCorner {
                background: url("${ Config.getInstance().getBaseURL() }/images/grey_corners.png") no-repeat scroll 0 0 transparent;
                float: left;
                height: 15px;
                width: 15px;
            }
            .rightCorner {
                background: url("${ Config.getInstance().getBaseURL() }/images/grey_corners.png") no-repeat scroll -15px 0 transparent;
                float: right;
                height: 15px;
                width: 15px;
            }
            #errorBoxContainer {
                width: 340px;
                padding-top: 20px;
            }
            #errorBoxContent {
                background: url("${ Config.getInstance().getBaseURL() }/images/grey_gradient.png") repeat-x scroll left bottom #ECECEC;
                padding: 20px 20px 50px;
            }
            #errorBoxLink {
                padding-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="pageHeader" align="center">
                <a href="${ Config.getInstance().getBaseURL() }/">
                    <img alt="logo" class="headerLogo" src="${ Config.getInstance().getSystemIconURL("logoIndico") }" />
                </a>
            </div>
            <div align="center">
                <div id="errorBoxContainer" align="center">
                    <div class="leftCorner"></div>
                    <div class="rightCorner"></div>
                    <div id="errorBoxContent">
                        <h1>${ errorTitle }</h1>
                        <div id="errorBoxText">
                            ${ errorText }<br />
                            ${ _("Click the following link to go to the main page:") }
                        </div>
                        <div id="errorBoxLink">
                            <a href="${ Config.getInstance().getBaseURL() }/">${ _("Indico main page") }</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
</html>
