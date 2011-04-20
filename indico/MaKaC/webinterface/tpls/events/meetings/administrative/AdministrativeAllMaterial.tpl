<%inherit file="Administrative.tpl"/>

<%!
  allMaterial = True
  hideTime = True
%>

<%block name="eventMaterial">
    % if len(conf.getAllMaterialList()) > 0:
        % for material in conf.getAllMaterialList():
            <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a>&nbsp;
        % endfor
    % endif
</%block>
