
    <% if ShowKeepValues: %>
    <tr>
      <td>
        <input id="keepPDFOptions" type="checkbox" value="keepPDFOptions" name="keepPDFOptions" checked />
        <label for="keepPDFOptions"><%= _("Keep these values for next time")%></label>
        <% inlineContextHelp( _('If you produce badges with these PDF options, they will be kept the next time so that you do not have to input them again.') ) %>
      </td>
    </tr>
    <% end %>
    <tr>
      <td>
        <table>
          <tbody>
            <tr>
              <td>
              </td>
              <td style="text-align: center; vertical-align:bottom; white-space: nowrap;">
                <%= _("Top margin")%>
                <% inlineContextHelp( _('Space between the first row of badges and the top edge of the paper.') ) %>
                <br />
                <input name="marginTop" size="3" value="<%=PDFOptions.getTopMargin()%>" />
              </td style="text-align: left; vertical-align:bottom;" >
              <td>
                 <span>
                    <%= _("Values are in cm.")%><br />
                    <%= _("Decimals are allowed.")%>
                    <% inlineContextHelp( _('You can write values such as &quot;1&quot;, &quot;1.25&quot;, etc.<br />They will be interpreted as <strong>cm</strong>.') ) %>
                 </span>
              </td>
             </tr>
             <tr>
              <td style="text-align: right; vertical-align: middle;" >
                <% inlineContextHelp( _('Space between the first column of badges and the left edge of the paper.') ) %>
                <%= _("Left margin")%>
                <input name="marginLeft" size="3" value="<%=PDFOptions.getLeftMargin()%>" />
              </td>
              <td>
                <img src="<%= Config.getInstance().getSystemIconURL("badgeMargins") %>" alt="<%= _("Badge Margins")%>" title="" />
              </td>
              <td style="text-align: left; vertical-align: middle;">
                <input name="marginRight" size="3" value="<%=PDFOptions.getRightMargin()%>" />
                <%= _("Right margin")%>
                <% inlineContextHelp( _('Minimum space between the last column of badges and the right edge of the paper.') ) %> 
              </td>
            </tr>
            <tr>
              <td style="text-align: right; vertical-align: top;">
                <% inlineContextHelp( _('Space between 2 columns of badges.') ) %>
                <span style="color:#B02B2C;"><%= _("Margin between columns")%></span><input style="margin-left: 5px;" name="marginColumns" size="3" value="<%=PDFOptions.getMarginColumns()%>" />
              </td>
              <td style="text-align: center; vertical-align: top;">
                <input name="marginBottom" size="3" value="<%=PDFOptions.getBottomMargin()%>" /><br />
                <%= _("Bottom margin")%>
                <% inlineContextHelp( _('Minimum space between the last row of badges and the botttom edge of the paper.') ) %>
              </td>
              <td style="text-align: left; vertical-align: top;">
                <input style="margin-right: 5px;" name="marginRows" size="3" value="<%=PDFOptions.getMarginRows()%>" /><span style="color:#4096EE;"><%= _("Margin between rows")%></span>
                <% inlineContextHelp( _('Space between 2 rows of badges.') ) %>
              </td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
    <tr>
      <td>
        <% checked = ['', 'checked'][PDFOptions.getDrawDashedRectangles()] %>
        <input id="drawDashedRectangles" type="checkbox" value="drawDashedRectangles" name="drawDashedRectangles" <%= checked %> />
        <label for="drawDashedRectangles"><%= _("Draw a dashed rectangle around each badge.")%></label>
      </td>
    </tr>
    <tr>
      <td>
        <%= _("Page size")%>
        <select name="pagesize">
            <% for pagesizeName in PagesizeNames : %>
                <% if pagesizeName == PDFOptions.getPagesize(): %>
                    <% selectedText = " SELECTED" %>
                <% end %>
                <% else: %>
                    <% selectedText = "" %>
                <% end %>
                <option <%= selectedText %>>
                    <%= pagesizeName %>
                </option>            
            <% end %>
        </select>
      </td>
    </tr>
    <% if ShowTip: %>
    <tr>
      <td>
        <div style="border-top:1px solid; margin-right: 10px; margin-top:1em;">
          <strong>Tip</strong><%= _(": if your printer does not align the badges correctly, you can tweak the margins.")%><br />
          <em>Example</em>: your left and right margins are 1.5 cm each, but your printer prints everything 1 mm on the left.<br />
          <%= _("In that case, you can use a left margin of 1.6 cm and a right margin of 1.4 cm to compensate.")%><br />
          <%= _("If you increase a margin, do not forget to decrease the opposite one or maybe Indico will think there is less space for printing badges, and the number of rows / columns will change.")%>
        </div>
      </td>
    </tr>
    <% end %>
