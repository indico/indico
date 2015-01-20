<%namespace name="common" file="../../include/Common.tpl"/>
<%!
    minutes = False
    checkEndTime = False
    olist = False
    showDescriptionTitle = False
    checkOwnerLocation = True
%>

<%include file="../../include/ApplyParticipation.tpl" />

<table class="eventWrapper" cellpadding="0">
<tr>
  <td>
  <%include file="include/Header.tpl"/>
  <% order = 1%>
  % for index, item in enumerate(entries):
    <%
        date = getDate(item.getAdjustedStartDate(timezone))
        previousItem = entries[index - 1] if index - 1 >= 0 else None
        nextItem = entries[index + 1] if index + 1 < len(entries) else None
    %>
    % if not previousItem or date != getDate(previousItem.getAdjustedStartDate(timezone)):
        <a name="${getDate(item.getAdjustedStartDate(timezone))}"></a>
        <br/>&nbsp;<br/>&nbsp;<span style="font-weight:bold;">${prettyDate(item.getAdjustedStartDate(timezone))}</span>
        <hr/>
    % endif
    % if getItemType(item) in ['Contribution','Break']:
        <table class="dayList" cellspacing="0" cellpadding="4">
    % endif
    <%include file="include/${getItemType(item)}.tpl" args="item=item, parent=conf,minutes=self.attr.minutes, olist=self.attr.olist, checkEndTime=self.attr.checkEndTime, order=order, showDescriptionTitle = self.attr.showDescriptionTitle, checkOwnerLocation=self.attr.checkOwnerLocation"/>
    % if getItemType(item) in ['Contribution','Break']:
        </table>
    % endif
    % if getItemType(item) == 'Contribution':
       <%order+=1%>
    % elif getItemType(item) == 'Session':
       <% order+= item.getSession().getNumberOfContributions() %>
    % endif

% endfor
  </td>
</tr>
</table>

