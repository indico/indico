<div id="PDFOptionsContainer" style="max-width:550px;margin:10px;">
    <div class="message neutral">
        <div class="toolbar-container">
          % if ShowKeepValues:
            <div class="element">
              <input id="keepPDFOptions" type="checkbox" value="keepPDFOptions" name="keepPDFOptions" />
              <label for="keepPDFOptions">${ _("Keep these values for next time")}</label>
              ${inlineContextHelp(_('If you produce badges with these PDF options, they will be kept the next time so that you do not have to input them again.') )}
            </div>
          % endif
            <div class="element">
            <% checked = ['', 'checked'][PDFOptions.getDrawDashedRectangles()] %>
              <input id="drawDashedRectangles" type="checkbox" value="drawDashedRectangles" name="drawDashedRectangles" ${ checked } />
              <label for="drawDashedRectangles">${ _("Draw a dashed rectangle around each badge")}</label>
            </div>
            <div class="element">
              <% checked = ['', 'checked'][PDFOptions.getLandscape()] %>
              <input id="landscape" type="checkbox" value="1" name="landscape" ${ checked } />
              <label for="landscape">${ _("Use landscape page orientation")}</label>
            </div>
        </div>
        <div class="toolbar-container">
          ${ _("Page size:")}
          <select name="pagesize">
              % for pagesizeName in PagesizeNames :
                  % if pagesizeName == PDFOptions.getPagesize():
                  <option selected="SELECTED">
                  % else:
                  <option>
                  % endif
                      ${ pagesizeName }
                  </option>
              % endfor
          </select>
        </div>
        <div class="toolbar-clearer"></div>
    </div>
    <table style="margin:auto;">
      <tbody>
        <tr>
          <td>
          </td>
          <td style="text-align: center; vertical-align:bottom; white-space: nowrap;">
            ${ _("Top margin")}
            ${inlineContextHelp(_('Space between the first row of badges and the top edge of the paper.') )}
            <br />
            <input name="marginTop" size="3" value="${PDFOptions.getTopMargin()}" />
          </td style="text-align: left; vertical-align:bottom;" >
          <td>
          </td>
         </tr>
         <tr>
          <td style="text-align: right; vertical-align: middle;" >
            ${inlineContextHelp(_('Space between the first column of badges and the left edge of the paper.') )}
            ${ _("Left margin")}
            <input name="marginLeft" size="3" value="${PDFOptions.getLeftMargin()}" />
          </td>
          <td>
            <img src="${ Config.getInstance().getSystemIconURL("badgeMargins") }" alt="${ _("Badge Margins")}" title="" />
          </td>
          <td style="text-align: left; vertical-align: middle;">
            <input name="marginRight" size="3" value="${PDFOptions.getRightMargin()}" />
            ${ _("Right margin")}
            ${inlineContextHelp(_('Minimum space between the last column of badges and the right edge of the paper.') )}
          </td>
        </tr>
        <tr>
          <td style="text-align: right; vertical-align: top;">
          </td>
          <td style="text-align: center; vertical-align: top;">
            <input name="marginBottom" size="3" value="${PDFOptions.getBottomMargin()}" /><br />
            ${ _("Bottom margin")}
            ${inlineContextHelp(_('Minimum space between the last row of badges and the botttom edge of the paper.') )}
          </td>
          <td style="text-align: left; vertical-align: top;">
          </td>
        </tr>
        <tr>
          <td colspan=2>
            <span style="color:#B02B2C;">${ _("Margin between columns")}</span>
            ${inlineContextHelp(_('Space between 2 columns of badges.') )}
          </td>
          <td>
            <input name="marginColumns" size="3" value="${PDFOptions.getMarginColumns()}" />
          </td>
        </tr>
          <td colspan=2>
            <span style="color:#4096EE;">${ _("Margin between rows")}</span>
            ${inlineContextHelp(_('Space between 2 rows of badges.') )}
          </td>
          <td>
            <input name="marginRows" size="3" value="${PDFOptions.getMarginRows()}" />
          </td>
        <tr>
          <td colspan=3>
            ${ _("Values are in cm, decimals are allowed.")}
            ${inlineContextHelp(_('You can write values such as &quot;1&quot;, &quot;1.25&quot;, etc.<br />They will be interpreted as <strong>cm</strong>.') )}
          </td>
        </tr>
      </tbody>
    </table>
% if ShowTip:
    <div class="message info">
      <div>
        <strong>Tip</strong>${ _(": if your printer does not align the badges correctly, you can tweak the margins.")}
      </div>
      <div>
        <strong>Example</strong>: ${_("If your left and right margins are 1.5 cm each, but your printer prints everything 1 mm to the left, ")}
        ${ _("you could use a left margin of 1.6 cm and a right margin of 1.4 cm to compensate.")}
        ${ _("If you increase a margin, do not forget to decrease the opposing one to avoid Indico thinking there is less space for printing badges, and the number of rows / columns will change.")}
      </div>
    </div>
% endif
</div>
