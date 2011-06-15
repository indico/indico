<%inherit file="Administrative.tpl"/>

<%!
  allMaterial = True
  hideTime = True
%>

<%block name="eventMaterial">
    % if len(conf.getAllMaterialList()) > 0:
        % for material in conf.getAllMaterialList():
            % if material.canView(accessWrapper):
                <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a>&nbsp;
            % endif
        % endfor
    % endif
</%block>
