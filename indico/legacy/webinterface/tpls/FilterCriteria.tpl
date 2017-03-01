<div class="CRLDiv" style="display: none;" id="filterMenu">
<table width="100%" cellpadding="0" cellspacing="0" valign="top"  style="padding-bottom: 10px;">

<% counter = 0 %>

% for name, section in content:
  % if counter % 4 == 0:
    <tr style="padding-bottom: 10px;">
  % endif

  <td style="width:25%; padding-left: 10px;" valign="top" align="left">
    <table class="filterTable" id="${ name }">
      ${ section }
    </table>
  </td>

  <% counter += 1 %>
  % if counter % 4 == 0:
    </tr>
  % endif

% endfor
</table>
${ extra }
<div style="text-align: center;"><input type="submit" class="btn" name="OK" value="${ _("Apply filter")}"></div></div>
