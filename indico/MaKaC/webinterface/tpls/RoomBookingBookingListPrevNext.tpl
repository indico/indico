
<% if withPrevNext: %>
    <table style="width: 98%; border-collapse: collapse; margin-top: 5px; background-color: #F5F5F5">
    <tr>
    <td><a href="<%= prevURL %>" style="font-size: xx-small;">&lt; <%= _("previous")+" "%> <%= periodName %></a></td>
    <td style="text-align: center;">
        <form id="dateSelect<%= prevNextNo %>" action="<%= urlHandlers.UHRoomBookingBookingList.getURL() %>" method="POST">
            <% if title and rh._ofMyRooms: %>
                <input type="hidden" id="ofMyRooms" name="ofMyRooms" value="on" />
            <% end %>
            <% elif rh._onlyMy: %>
                <input type="hidden" id="onlyMy" name="onlyMy" value="on" />
            <% end %>
            <% elif rh._allRooms: %>
                <input type="hidden" id="roomGUID" name="roomGUID" value="allRooms" />
            <% end %>
            <% else: %>
                <% for room in rh._roomGUIDs: %>
                    <input type="hidden" id="roomGUID" name="roomGUID" value="<%= room %>" />
                <% end %>
            <% end %>
            <% if rh._onlyPrebookings: %>
                <input type="hidden" id="onlyPrebookings" name="onlyPrebookings" value="on" />
            <% end %>
            <% if rh._onlyBookings: %>
                <input type="hidden" id="onlyBookings" name="onlyBookings" value="on" />
            <% end %>
            <input type="hidden" id="sDay" name="sDay" />
            <input type="hidden" id="sMonth" name="sMonth" />
            <input type="hidden" id="sYear" name="sYear" />
            <input type="hidden" id="eDay" name="eDay" />
            <input type="hidden" id="eMonth" name="eMonth" />
            <input type="hidden" id="eYear" name="eYear" />
            <input type="hidden" id="reason" name="reason" />
            <%= verbosePeriod %>
        </form>
    </td>
    <td style="text-align: right;"><a href="<%= nextURL %>" style="font-size: xx-small;"><%= _("next")+" "%> <%= periodName %> &gt;</a></td>
    </tr>
    <tr>
        <td colspan="3" style="text-align: center"><a href="#" style="font-size: x-small;" id="selectDateIcon<%= prevNextNo %>"><%=_("change period") %></a></td>
    </tr>
    </table>

    <script type="text/javascript">

    $('selectDateIcon<%= prevNextNo %>').observe('click', function() {
        var dlg = new DateRangeSelector('<%= startD %>', '<%= endD %>', function(startDate, endDate) {
            var form = $('dateSelect<%= prevNextNo %>');
            form['sDay'].value = startDate.getDate();
            form['sMonth'].value = startDate.getMonth() + 1;
            form['sYear'].value = startDate.getFullYear();

            form['eDay'].value = endDate.getDate();
            form['eMonth'].value = endDate.getMonth() + 1;
            form['eYear'].value = endDate.getFullYear();

            form.submit();
        }, '<%=_("Choose Period") %>', true);
        dlg.open();
    });
    </script>

<% end %>
