<%inherit file="Administrative.tpl"/>

<%!
  allMaterial = False
  hideTime = True
  minutes = True
%>

<%block name="header">
    <br/>&nbsp;<br/>
    <div class="eventHeader">
        ASSOCIATION DU PERSONNEL<br/>
        <span class="CERNTitle"> CERN </span>
        STAFF ASSOCIATION
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