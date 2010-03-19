<script type="text/javascript">

	// Removes red background from form fields.
	// Often calleed in the beginning of validation.
	function period_clean_redouts( f1 )
	{
        f1.sDay.className = f1.sMonth.className = f1.sYear.className = f1.sdate.className = '';
        f1.eDay.className = f1.eMonth.className = f1.eYear.className = f1.edate.className = '';
        f1.sTime.className = f1.eTime.className = '';
        f1.repeatability.className = '';
    }

    // Comments the repeatition for user, to make it clear
    function set_repeatition_comment()
    {
        var repTypeSel = $('repeatability')
        var repCom = $('repComment')
        var s = ''
        var repType = parseInt( repTypeSel.value, 10 )
        if ( repType > 0 )
        {
            date = new Date( parseInt( $F('sYear'), 10 ), parseInt( $F('sMonth')-1, 10 ), parseInt( $F('sDay'), 10 ) )
            weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            s = 'on ' + weekDays[date.getDay()]
            if ( repType == 4 )
            {
                weekNr = Math.floor( date.getDate() / 7 ) + 1
                postfix = ['st', 'nd', 'rd', 'th', 'th']
                weekNrStr = 'the ' + weekNr + postfix[weekNr-1] + ' '
                s = 'on ' + weekNrStr + weekDays[date.getDay()] + ' of a month'
            }
        }
        repCom.innerHTML = s

/*
        skipConflicts = $( '' );
        if ( skipConflicts )
        {
            if ( repType == 0 ) skipConflicts.hide();
            else skipConflicts.show();
        }
*/
    }

    IndicoUI.executeOnLoad(function()
    {
        var startDate = IndicoUI.Widgets.Generic.dateField_sdate(false,null,['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField_edate(false,null,['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);

        /* In case the date changes, we need to check whether the start date is greater than the end date,
        and if it's so we need to change it */
        startDate.observe(function(value) {
            if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
                endDate.set(startDate.get());
                endDate.dom.onchange();
                set_repeatition_comment();
            }
        });

        endDate.observe(function(value) {
            if ( IndicoUtil.parseDate(startDate.get()) > IndicoUtil.parseDate(endDate.get()) ) {
                startDate.set(endDate.get());
                startDate.dom.onchange();
                set_repeatition_comment();
            }
        });

       <% if startDT.day != '': %>
            startDate.set('<%= startDT.day %>/<%= startDT.month %>/<%= startDT.year %>');
        <% end %>

        <% if endDT.day != '': %>
            endDate.set('<%= endDT.day %>/<%= endDT.month %>/<%= endDT.year %>');
        <% end %>

     });
</script>
                                        <tr id="sdatesTR" >
                                            <td class="subFieldWidth" align="right" ><small> <%= _("Start Date")%>&nbsp;&nbsp;</small></td>
                                            <td class="blacktext">
                                                <span id="sDatePlace"></span>
                                                <input type="hidden" value="<%= startDT.day %>" name="sDay" id="sDay"/>
                                                <input type="hidden" value="<%= startDT.month %>" name="sMonth" id="sMonth"/>
                                                <input type="hidden" value="<%= startDT.year %>" name="sYear" id="sYear"/>
                                            </td>
                                          </tr>
                                         <tr id="edatesTR" >
                                            <td class="subFieldWidth" align="right" ><small> <%= _("End Date")%>&nbsp;&nbsp;</small></td>
                                            <td>
                                                <span id="eDatePlace"></span>
                                                <input type="hidden" value="<%= endDT.day %>" name="eDay" id="eDay"/>
                                                <input type="hidden" value="<%= endDT.month %>" name="eMonth" id="eMonth"/>
                                                <input type="hidden" value="<%= endDT.year %>" name="eYear" id="eYear"/>
                                            </td>
                                        </tr>
                                        <tr id="hoursTR" >
                                            <td align="right" ><small> <%= _("Hours")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input name="sTime" id="sTime" maxlength="5" size="5" type="text" value="<%= startT %>" onchange="" /> &nbsp;&mdash;&nbsp;
                                                <input name="eTime" id="eTime" maxlength="5" size="5" type="text" value="<%= endT %>" onchange="" />
                                                <span id="holidays-warning" style="color: Red; font-weight:bold;"></span>
                                            </td>
                                        </tr>
                                        <tr id="repTypeTR" >
                                            <td align="right" ><small> <%= _("Type")%>&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext" >
                                                <select name="repeatability" id="repeatability" onchange="set_repeatition_comment();">
                                                <% sel = [ "", "", "", "", "", "" ]; %>
                                                <% if repeatability == None: %>
                                                <%     sel[5] = 'selected="selected"' %>
                                                <% end %>
                                                <% if repeatability != None: %>
                                                <%     sel[repeatability] = 'selected="selected"' %>
                                                <% end %>
                                                    <option <%= sel[5] %> value="None"> <%= _("Single day")%></option>
                                                    <option <%= sel[0] %> value="0"> <%= _("Repeat daily")%></option>
                                                    <option <%= sel[1] %> value="1"> <%= _("Repeat once a week")%></option>
                                                    <option <%= sel[2] %> value="2"> <%= _("Repeat once every two weeks")%></option>
                                                    <option <%= sel[3] %> value="3"> <%= _("Repeat once every three weeks")%></option>
                                                    <option <%= sel[4] %> value="4"> <%= _("Repeat every month")%></option>
                                                </select>
                                                <span id="repComment" style="margin-left: 12px"></span>
                                                <% contextHelp( 'repeatitionHelp' ) %>
                                            </td>
                                        </tr>
