
  <table class="noticeMain" style="text-align: center;">
    <tr>
      <td class="title"> ${ _("Evaluation")}&nbsp;${status}</td>
    </tr>
    <tr>
      <td class="td">

        <br><br>
        <table class="noticeInside" style="text-align: center; margin: auto;">
          <tr>
            <td> ${ _("Your information has been saved.<br/><br/>Thank you for your participation!")}</td>
          </tr>
        </table>

        % if redirection!=None:
          <br><br>
          <script type="text/javascript">
            function redirUrl() { return "${redirection}"; }
            document.writeln("<input class='btn' type='button' value='OK' onclick='self.location.href=redirUrl()'/>");
          </script>
          <noscript>
            <a href="${redirection}">[ OK ]</a>
          </noscript>
        % endif

      </td>
    </tr>
  </table>
