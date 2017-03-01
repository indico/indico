<div style="color: #B14300; font-family: serif; clear:both;font-size:40px;width:100%;text-align:center;margin-top:30px;margin-bottom:50px">${ _("Error 404: Page not found") }</div>
<div style="font-family: serif;clear:both;font-size:20px;width:100%;text-align:center">${ _("The resource you are looking for is not stored in our server.") }</div>
<div style="font-family: serif;clear:both;font-size:20px;width:100%;text-align:center">${ _("Sorry for the inconvenience.") }</div>
% if goBack:
    <div style="clear:both;font-size:16px;width:100%;text-align:center;margin-top:30px;">
        <a href="${ goBack }"> Click here to go back. </a>
    </div>
% endif
