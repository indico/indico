<%inherit file="AdministrativeAllMaterial.tpl"/>
<%!
  allMaterial = True
  hideTime = True
  showOrder=True
%>

<%block name="header">
     <br/>&nbsp;<br/>
    <table class="eventHeader">
        <tr>
            <td>
                <img src="${Config.getInstance().getBaseURL()}/images/CERNLogo.jpg" />
            </td>
            <td>
                <div class="eventHeader">
                    CAISSE DE PENSIONS <br />
                    <span class="CERNTitle"> CERN </span>
                    PENSION FUND
                </div>
            </td>
            <td>
                <img src="${Config.getInstance().getBaseURL()}/images/eso-logo.gif" />
            </td>
        </tr>
    </table>
                <div align="center">
                <hr width="50%"/>
            </div>
</%block>

<%block name="printSchedule" args="showOrder">
    ${parent.printSchedule(True)}
</%block>
