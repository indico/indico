<% declareTemplate(newTemplateStyle=True) %>

<div><span>
<a id="scroll_down" name="top"></a>
<br />
</span></div>

<table>
  <tr>
    <td width="590px" valign="top">
        <b>1. <%= _("Select a record:") %></b>
        <br /> <!-- line breaks to make the pretty boxes below to line up -->
        <br />
        <br />
        <div class="nicebox">
        <div class="RMMatchPane">
            <% for talk in Talks: %>
                <% IndicoID = talk["IndicoID"] %>

                  <span>
                    <table cellspacing="0" cellpadding="0" border="0">
                    <tr>
                    <td width="380px">
<!--
                        <tt><b><%= {'conference':      "E&nbsp;",
                                 'session':         "&nbsp;S&nbsp;",
                                 'contribution':    "&nbsp;&nbsp;C&nbsp;",
                                 'subcontribution': "&nbsp;&nbsp;&nbsp;SC&nbsp;"}[talk["type"]] %></b></tt>
                        <%= talk["titleshort"] %><br />&nbsp;
-->
                        <div id="div<%= IndicoID %>" class="RMtalkDisplay" onclick="RMtalkSelect('<%= IndicoID %>')" onmouseover="RMtalkBoxOnHover('<%= IndicoID %>');" onmouseout="RMtalkBoxOffHover('<%= IndicoID %>');">
                            <tt><b><%= {'conference':      "E&nbsp;",
                                     'session':         "S&nbsp;&nbsp;",
                                     'contribution':    "C&nbsp;&nbsp;&nbsp;",
                                     'subcontribution': "SC&nbsp;&nbsp;&nbsp;&nbsp;"}[talk["type"]] %></b></tt>
                            <%= talk["titleshort"] %><br />&nbsp;
                            <tt><%= {'conference':      "&nbsp;&nbsp;",
                                     'session':         "&nbsp;&nbsp;&nbsp;",
                                     'contribution':    "&nbsp;&nbsp;&nbsp;&nbsp;",
                                     'subcontribution': "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"}[talk["type"]] %></b></tt>
                            <% if talk["speakers"] != '': %>
                            <%=    talk["speakers"] %>
                            <% end %>
                        </div>
                    </td>
                    <td width="50px">
                        <% if talk["LOID"] != '': %>
                            <div class="RMcolumnStatusNone" style="background-image: url('<%= "/indico/images/RecordingManagerMicalaCheck.png" %>');">
                            &nbsp;</div>
                        <% end %>
                        <% else: %>
                            <div class="RMcolumnStatusNone">
                            </div>
                        <% end %>
                    </td>
                    <td width="50px">
                        <% if talk["CDSID"] != 'none' and talk["CDSID"] != 'pending': %>
                            <div class="RMcolumnStatusCDSDone" id="divCDS<%= talk["IndicoID"] %>" onclick="RMCDSDoneClick('<%= talk["CDSURL"] %>')" onmouseover="RMCDSDoneOnHover('<%= talk["IndicoID"] %>')" onmouseout="RMCDSDoneOffHover('<%= talk["IndicoID"] %>')">
                            </div>
                        <% end %>
                        <% elif talk["CDSID"] == 'pending': %>
                            <div class="RMcolumnStatusCDSPending">
                            </div>
                        <% end %>
                        <% else: %>
                            <div class="RMcolumnStatusNone">
                            </div>
                        <% end %>
                    </td>
                    <td width="50px">
                        <% if talk["IndicoLink"] == True: %>
                            <div class="RMcolumnStatusNone" style="background-image: url('<%= "/indico/images/RecordingManagerIndicoCheck.png" %>');">
                            </div>
                        <% end %>
                        <% else: %>
                            <div class="RMcolumnStatusNone">
                            </div>
                        <% end %>
                    </td>
                    </tr>
                    </table>
                    </span>
            <% end %>
        </div>
        </div>
    </td>
    <td width="620px" valign="top">
        <b>2. <%= _("Select content type: ") %></b>
        <span id="RMbuttonPlainVideo" class="RMbuttonDisplay" onclick="RMbuttonModeSelect('plain_video')" onmouseover="RMbuttonModeOnHover('plain_video');" onmouseout="RMbuttonModeOffHover('plain_video')"><%= _("plain video") %></span>
        &nbsp;<%= _(" or ") %>&nbsp;
        <span id="RMbuttonWebLecture" class="RMbuttonDisplay" onclick="RMbuttonModeSelect('web_lecture')" onmouseover="RMbuttonModeOnHover('web_lecture');" onmouseout="RMbuttonModeOffHover('web_lecture')"><%= _("web lecture") %></span>
        <div id="RMrightPaneWebLecture" class="RMHolderPaneDefaultInvisible">
            <br />
            <b>3. <%= _("Select an orphan lecture object: ") %></b>
        <div class="nicebox">
        <div class="RMMatchPane">
            <% for orphan in Orphans: %>
                <% lectureDBid = orphan["id"] %>
                <% LOID        = orphan["LOID"] %>
                <div id="lo<%= lectureDBid %>" class="RMLODisplay" onclick="RMLOSelect(<%= lectureDBid %>)" onmouseover="RMLOBoxOnHover(<%= lectureDBid %>);" onmouseout="RMLOBoxOffHover(<%= lectureDBid %>);">
                    <table>
                        <tr width="100%">
                            <td width="30%" valign="top">
                                time: <%= orphan["time"] %><br />
                                date: <%= orphan["date"] %><br />
                                box:  <%= orphan["box"]  %>
                            </td>
                            <td width="70%" align="right">
                                <img src="<%= PreviewURL %><%= LOID %>/video0001.jpg">
                                <img src="<%= PreviewURL %><%= LOID %>/video0002.jpg"><br />
                            </td>
                        </tr>
                        <tr width="100%">
                            <td width="100%" colspan="2">
                            <img src="<%= PreviewURL %><%= LOID %>/content0001.jpg">
                            <img src="<%= PreviewURL %><%= LOID %>/content0002.jpg">
                            <img src="<%= PreviewURL %><%= LOID %>/content0003.jpg">
                            <img src="<%= PreviewURL %><%= LOID %>/content0004.jpg">
                            </td>
                        </tr>
                    </table>
                </div>
            <% end %>
        </div>
        </div>
        </div>
        <div id="RMrightPanePlainVideo" class="RMHolderPaneDefaultInvisible">
            <br />
            <b>3. <%= _("Select options: ") %></b>
            <div class="RMMatchPane" style="height: 200px;">
                Select video aspect ratio:
                <input type="radio" name="talks" value="standard" id="RMvideoFormat4to3" onclick="RMchooseVideoFormat('standard')" checked>
                <label for="RMvideoFormat4to3">standard (4/3)</label>
                &nbsp;&nbsp;&nbsp;
                <input type="radio" name="talks" value="wide" id="RMvideoFormat16to9" onclick="RMchooseVideoFormat('wide')">
                <label for="RMvideoFormat16to9">wide (16/9)</label>
            </div>
        </div>
    </td>
  </tr>
</table>

<div id="RMlowerPane" class="RMHolderPaneDefaultVisible" style="margin-left: 150px;">
    <span>
        <br />
        <b>4. <%= _("Select language(s) in which the talk was given") %></b>
        <br />
        <!-- http://www.loc.gov/marc/languages/ -->

        <input type="checkbox" value="<%= LanguageList[0][0] %>" id="RMLanguagePrimary" onclick="RMLanguageTogglePrimary('<%= LanguageList[0][0] %>')"><%= LanguageList[0][1] %></input>
        &nbsp;&nbsp;&nbsp;&nbsp;
        <input type="checkbox" id="RMLanguageSecondary" onclick="RMLanguageToggleSecondary('<%= LanguageList[1][0] %>')"><%= LanguageList[1][1] %></input>
        &nbsp;&nbsp;&nbsp;&nbsp;
        <input type="checkbox" name="Other" value="other" id="RMLanguageOther" onclick="RMLanguageToggleOther()">Other</input>
        <select id="RMLanguageOtherSelect">
            <option value="chooseOne" onclick="RMLanguageSelectOther(0)">-- <%= _('Choose one') %> --</option>
            <% for languageCode, languageName in LanguageList: %>
                <% if languageName != 'English' and languageName != 'French': %>
                <option value="<%=languageCode%>" onclick="RMLanguageSelectOther('<%=languageCode%>')"><%=languageName%></option>
                <% end %>
            <% end %>
        </select>
        <span id="RMSelectLanguage">
        <!--  Javascript button here -->
        </span>

<!--         <input type="button" disabled="" id="RMbuttonCreateCDSRecord" onclick="RMCreateCDSRecord()" value=<%= _("\"Create CDS record\"") %> /> -->
    </span>
    <span>
        <br />
        <b>5. <%= _("Create CDS record (and update micala database)") %></b>
        <br />
        <span id="RMbuttonCreateCDSRecord">
        <!--  Javascript button here -->
        </span>
        <span id="RMMatchSummaryMessage">
        </span>

<!--         <input type="button" disabled="" id="RMbuttonCreateCDSRecord" onclick="RMCreateCDSRecord()" value=<%= _("\"Create CDS record\"") %> /> -->
    </span>
    <br />
    <br />
    <br />
    <span>
        <b>6. <%= _("Create Indico link to CDS record") %></b>
        <br />
        <div id="RMbuttonCreateIndicoLink">
        <!--  Javascript button here -->
        </div>
<!--         <input type="button" disabled="" id="RMbuttonCreateIndicoLink" onclick="RMcreateIndicoLink()" value="<%= _("Create Indico link") %>" /> -->
    </span>
</div>

<script type="text/javascript">
    var RM_orphans = <%= jsonEncode(Orphans) %>;

    var RMselectedTalkId    = '';
    var RMselectedLOID      = '';
    var RMselectedTalkName  = '';
    var RMselectedLOName    = '';
    var RMviewMode          = '';
    var RMvideoFormat       = 'standard';
    var RMLanguageFlagPrimary   = true;
    var RMLanguageFlagSecondary = false;
    var RMLanguageFlagOther     = false;
    var RMLanguageValuePrimary   = '<%= LanguageList[0][0] %>';
    var RMLanguageValueSecondary = '<%= LanguageList[1][0] %>';
    var RMLanguageValueOther    = 0;

    // Pass the metadata we need for each talk to JavaScript
    var RMTalkList = {
    <% for talk in Talks: %>
    "<%= talk["IndicoID"]   %>": {
        "title":      "<%= talk["title"]      %>",
        "titleshort": "<%= talk["titleshort"] %>",
        "CDSID":      "<%= talk["CDSID"]      %>",
        "CDSURL":     "<%= talk["CDSURL"]     %>",
        "type":       "<%= talk["type"]       %>",
        "speakers":   "<%= talk["speakers"]   %>",
        "date":       "<%= talk["date"]       %>",
        "LOID":       "<%= talk["LOID"]       %>",
        "IndicoLink": "<%= talk["IndicoLink"] %>"
    },
    <% end %>
    };

    // Draw the two buttons, which start out as disabled until
    // the user has selected both talk and LO
    $E('RMbuttonCreateCDSRecord').set(ButtonCreateCDSRecord.draw());
    $E('RMbuttonCreateIndicoLink').set(ButtonCreateIndicoLink.draw());

</script>
