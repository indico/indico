  <table class="groupTable" style="text-align: left; width: 100%;" border="0" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="groupTitle">${ _("Available Styles")}
          ${inlineContextHelp(contextHelpText)}
        </td>
      </tr>
      <tr>
        <td>
          <form action="${ urlHandlers.UHAdminsAddStyle.getURL() }" method="POST">
          <input type="submit" class="btn" value="${ _("New")}">
          </form>
          <table cellspacing="1" align="center">
          <tr style="border-bottom: 1px;"><th>${ _("Name (ID)")}</th><th>${ _("XSL file")}</th><th>${ _("CSS file")}</th><th>${ _("Actions")}</th></tr>
          <% styles = styleMgr.getStylesheets().keys() %>
          <% styles.sort() %>
          % for style in styles: 
          <tr style="background-color: ${"#faa" if styleMgr.getXSLPath(style) == "" and style != 'static' else "lightgreen"}">
            <td align="right">${ styleMgr.getStylesheetName(style) } (${style})</td>
            <td align="center">${ _("found") if styleMgr.getXSLPath(style) else  _("not found")}</td>
            <td align="center">${ _("yes") if styleMgr.getCSSPath(style) else  _("no")}</td>
            <td>
            % if style == "static": 
            ${inlineContextHelp(_('This style cannot be deleted. this is the default style for conferences.<br/>It does not rely on an XSL file.'))}
            % else: 
            <a href="${urlHandlers.UHAdminsDeleteStyle.getURL(xslfile=style)}" onClick="if (!confirm('${ _("Are you sure you want to delete this style?")}')) { return false; }"><img border="0" src="${deleteIconURL}" alt="${ _("delete this style")}"></a>
            % endif
            </td>
          </tr>
          % endfor
          </table>
        </td>
      </tr>
      <tr>
        <td colspan="1" class="groupTitle">${ _("Styles for Lectures")}
        </td>
      </tr>
      <tr>
        <td>
          <form action="${ urlHandlers.UHAdminsStyles.getURL() }" method="POST">
          <input type="hidden" name="event_type" value="simple_event">
          <% styles = styleMgr.getStylesheetListForEventType("simple_event") %>
          <% styles.sort() %>
          ${ _("current list:")} <select name="xslfile">
          % for style in styles: 
          <option value="${style}"${'style="font-weight: bold;" selected' if style.strip()==styleMgr.getDefaultStylesheetForEventType("simple_event").strip() else ""}>${styleMgr.getStylesheetName(style)}${" (default)" if style.strip()==styleMgr.getDefaultStylesheetForEventType("simple_event").strip() else ""}</option>
          % endfor
          </select>
          <input type="submit" class="btn" name="action" value="${ _("default")}">
          <input type="submit" class="btn" name="action" value="${ _("delete")}"><br>
          ${ _("add new style:")}
           <select name="newstyle">
             % for style in styleMgr.getStylesheets(): 
               % if style not in styles: 
               <option value="${ style }">${styleMgr.getStylesheetName(style)}</option>
               % endif
             % endfor
           </select>
           <input type="submit" class="btn" name="action" value="${ _("add")}">
          </form>
        </td>
      </tr>
      <tr>
        <td colspan="1" class="groupTitle">${ _("Styles for Meetings")}
        </td>
      </tr>
      <tr>
        <td>
          <form action="${ urlHandlers.UHAdminsStyles.getURL() }" method="POST">
          <input type="hidden" name="event_type" value="meeting">
          <% styles = styleMgr.getStylesheetListForEventType("meeting") %>
          <% styles.sort() %>
          ${ _("current list:")} <select name="xslfile">
          % for style in styles: 
          <option value="${style}"${'style="font-weight: bold;" selected' if style.strip()==styleMgr.getDefaultStylesheetForEventType("meeting").strip() else ""}>${styleMgr.getStylesheetName(style)}${" (default)" if style.strip()==styleMgr.getDefaultStylesheetForEventType("meeting").strip() else ""}</option>
          % endfor
          </select>
          <input type="submit" class="btn" name="action" value="${ _("default")}">
          <input type="submit" class="btn" name="action" value="${ _("delete")}"><br>
          ${ _("add new style:")}
           <select name="newstyle">
             % for style in styleMgr.getStylesheets(): 
               % if style not in styles: 
               <option value="${ style }">${styleMgr.getStylesheetName(style)}</option>
               % endif
             % endfor
           </select>
           <input type="submit" class="btn" name="action" value="${ _("add")}">
          </form>
        </td>
      </tr>
      <tr>
        <td colspan="1" class="groupTitle">${ _("Styles for Conferences")}
        </td>
      </tr>
      <tr>
        <td>
          <form action="${ urlHandlers.UHAdminsStyles.getURL() }" method="POST">
          <input type="hidden" name="event_type" value="conference">
          <% styles = styleMgr.getStylesheetListForEventType("conference") %>
          <% styles.sort() %>
          ${ _("current list")}: <select name="xslfile">
          % for style in styles: 
          <option value="${style}"${'style="font-weight: bold;" selected' if style.strip()==styleMgr.getDefaultStylesheetForEventType("conference").strip() else ""}>${styleMgr.getStylesheetName(style)}${" (default)" if style.strip()==styleMgr.getDefaultStylesheetForEventType("conference").strip() else ""}</option>
          % endfor
          </select>
          <input type="submit" class="btn" name="action" value="${ _("default")}">
          <input type="submit" class="btn" name="action" value="${ _("delete")}"><br>
          ${ _("add new style:")}
           <select name="newstyle">
             % for style in styleMgr.getStylesheets(): 
               % if style not in styles: 
               <option value="${ style }">${styleMgr.getStylesheetName(style)}</option>
               % endif
             % endfor
           </select>
           <input type="submit" class="btn" name="action" value="${ _("add")}">
          </form>
        </td>
      </tr>
    </tbody>
  </table>