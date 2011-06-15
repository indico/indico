<%inherit file="Administrative.tpl"/>

<%!
  allMaterial = True
  hideTime = True
%>

<%block name="header">
     <br/>&nbsp;<br/>
    <table class="eventHeader">
        <tr>
            <td>
                <img src="./images/CERNLogo.jpg" />
            </td>
            <td>
                <div class="eventHeader">
                    CAISSE DE PENSIONS <br />
                    <span class="CERNTitle"> CERN </span>
                    PENSION FUND
                </div>
            </td>
            <td>
                <img src="./images/eso-logo.gif" />
            </td>
        </tr>
    </table>
                <div align="center">
                <hr width="50%"/>
            </div>
</%block>

<%block name="eventMaterial">
    % if len(conf.getAllMaterialList()) > 0:
        % for material in conf.getAllMaterialList():
            % if material.canView(accessWrapper):
               <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a>&nbsp;
            % endif
        % endfor
    % endif
</%block>

