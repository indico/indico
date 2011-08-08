<div class="container">

<table align="center" width="100%"><!--FFE6CC-->
    <tr>
        <td align="center"><font size="+2" color="#5294CC"><b> ${ _("Your request could not be completed")}</b></font></td>
    </tr>
    <tr>
        <td>
            <table width="90%" align="center">
                <tr>
                    <td><br>
            <table border ="0" cellpadding="4" cellspacing="1"
                                width="100%">
                 <tr>
                                <td style="background-color: #E5E5E5; text-align: center; font-size: 18px; color: #3366AA">${ area }${ msg }<br/>
                                % if contactInfo:
                                ${ _("If you consider you should have access, please contact:")}<span style="font-weight: bold;"> ${contactInfo}</span>
                                % endif
                                </td>
                            </tr>
                        </table>
                  </td>
                </tr>
                <tr>
                    <td><br></td>
                </tr>
                <tr>
                    <td>
                        <ul><font size="2" color="#5294CC" >
                            <li> ${ _("""You can go back to the precedent page by using the "Back" button of your browser.""")}
                            <li> ${ _("""You can try to refresh this page by using the "Refresh" button of your browser.""")}
                            <li> ${ _("You can contact the owner of this event.")}
                        </font></ul>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>



</div>
