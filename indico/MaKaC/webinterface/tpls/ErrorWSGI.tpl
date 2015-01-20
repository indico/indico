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
                background-color: #f0f0f0;
                font-family: Helvetica, Verdana, Sans;
                margin: 0;
                padding: 0;
                text-align: center;
            }

            a:link, a:visited {
                color: #007CAC;
                text-decoration: none;
            }

            a:hover {
                color: #E25300;
            }

            img.header-logo {
                border: none;
                height: 90px;
                margin: 50px 10px;
            }

            #error-box {

                padding: 2em;
                background-color: #e4e4e4;
                width: 400px;
                padding-top: 20px;
                display: inline-block;
                text-align: center;
                border-radius: .5em;
                border: 1px solid #d3d3d3;
            }

            #error-box h1 {
                color: #007CAC;
                font-size: 2em;
                padding-bottom: 10px;
            }

            .error-box-text {
                color: #666;
            }

            .error-box-small {
                margin-top: 2em;
                font-size: 0.8em;
            }

        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="page-header" align="center">
                <a href="${ Config.getInstance().getBaseURL() }/">
                    <img alt="logo" class="header-logo" src="${ Config.getInstance().getSystemIconURL("logoIndico") }" />
                </a>
            </div>
            <div id="error-box">
                <h1>${ errorTitle }</h1>
                <div class="error-box-text">
                    ${ errorText }
                </div>
                <div class="error-box-small">
                    <a href="${ Config.getInstance().getBaseURL() }/">${ _("Back to the main page") }</a>
                </div>
            </div>
        </div>
    </body>
</html>
