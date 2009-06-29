
  <table class="noticeMain" style="text-align: center;">
    <tr>
      <td class="title"> <%= _("Evaluation well")%>&nbsp;<%=status%></td>
    </tr>
    <tr>
      <td class="td">
      
        <br><br>
        <table class="noticeInside" style="text-align: center; margin: auto;">
          <tr>
            <td> <%= _("Your information have been well recorded.<br/><br/>Thank you for your contribution!")%></td>
          </tr>
        </table>
        
        <% if redirection!=None: %>
          <br><br>
          <script type="text/javascript">
            function redirUrl() { return "<%=redirection%>"; }
            document.writeln("<input class='btn' type='button' value='OK' onclick='self.location.href=redirUrl()'/>");
          </script>
          <noscript>
            <a href="<%=redirection%>">[ OK ]</a>
          </noscript>
        <% end %>
        
      </td>
    </tr>
  </table>
