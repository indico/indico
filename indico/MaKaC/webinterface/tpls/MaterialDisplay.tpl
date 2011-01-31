<table width="100%" align="center">
    <tr>

    </tr>
    <tr>
        <td align="center">
            <form action=<%= submitURL %> method="POST">
            <%= submitBtn %>
            </form>
        </td>
    </tr>
    <tr>
        <td>
	    <table align="center" width="95%" border="0" style="border: 1px solid #777777;">
            <tr>
                <td>&nbsp;</td>
            </tr>
            <tr>
              <td>
                <table>
		          <tr>
                    <td align="center"><font size="+1" color="black"><b><%= title %> <img src=<%= icon %> alt="file"></b></font></td>
		          </tr>
		          <tr>
		            <td width="100%">&nbsp;<td>
		          </tr>
		          <tr>
		            <td>
                       <table align="center">
                          <tr>
                             <td><pre><%= description %></pre></td>
                          </tr>
                        </table>
                    </td>
		          </tr>
                  <tr>
		            <td>
		                <table align="center" width="80%">
		                  <tr>
		                    <%= resources %>
					      </tr>
                        </table>
                    </td>

                </table>
              </td>
            </tr>
        </table>
        </td>
    <tr>
      <td align="center">
        <br>
        <form action=<%= submitURL %> method="POST">
        <%= submitBtn %>
        </form>
      </td>
    </tr>
</table>
