<table width="100%%" cellpadding="0" cellspacing="0" valign="top"  style="padding-bottom: 10px;">

<% counter = 0 %>

<% for name, section in content: %>
  <% if counter % 4 == 0: %>
    <tr style="padding-bottom: 10px;">
  <% end %>

  <td style="width:25%%; padding-left: 10px;" valign="top" align="left">
    <table class="filterTable" id="<%= name %>">
      <%= section %>
    </table>
  </td>

  <% counter += 1 %>
  <% if counter % 4 == 0: %>
    </tr>
  <% end %>

<% end %>
</table>
