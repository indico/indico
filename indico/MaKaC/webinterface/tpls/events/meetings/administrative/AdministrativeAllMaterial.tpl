<%inherit file="Administrative.tpl"/>

<%!
  allMaterial = True
  hideTime = True
%>

<%block name="eventMaterial">
  ${self.render_materials(conf)}
</%block>
