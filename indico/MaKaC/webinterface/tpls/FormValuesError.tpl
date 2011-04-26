<div class="container">


<table align="center" width="100%">
  <tr>
    <td align="center"><font size="+2" color="#5294CC"><b> ${ _("Your request could not be completed")}:</b></font></td>
  </tr>
  <tr>
    <td>
      <table width="90%" align="center">
        <tr>
          <td>
            <table border ="0" cellpadding="4" cellspacing="1" width="100%">
              <tr>
                <td bgcolor="#E5E5E5"><center><b><font size="+1" color="#3366AA">${ msg }</font></b></center></td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td><br></td>
        </tr>
        <tr>
          <td>
            <form action="" method="POST" onsubmit="return false;">
              <font size="+1">
                <center>
                  <input type="submit" class="btn" value="${ _("Go Back")}" onClick="javascript:history.back();">
                </center>
              </font>
            </form>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>

</div>
