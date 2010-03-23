
<% if withPrevNext: %>
    <% prevNextNo += 1%>
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
            <a href="#" id="selectDateIcon<%= prevNextNo %>"><img src="<%= Config.getInstance().getSystemIconURL('ical') %>" alt="Calendar" title="Select a Date" style="border: none; vertical-align: middle;" /></a>&nbsp;<%= verbosePeriod %>
        </form>
    </td>
    <td style="text-align: right;"><a href="<%= nextURL %>" style="font-size: xx-small;"><%= _("next")+" "%> <%= periodName %> &gt;</a></td>
    </tr>
    </table>

    <script language="JavaScript">

    /*   This avoids to create the same method twice.
         prevNextNo == 1 because the first time we have already
         incremented prevNextNo (see upper in this template).
    */
    <% if prevNextNo == 1 :%>
        function findDayPeriodFromDTString(sDate, eDate)
        {

            dateRE = /^(...) (\d+)\/(\d+)\/(\d+)$/;

            var m1 = dateRE.exec(sDate);
            var m2 = dateRE.exec(eDate);

            var sd = new Date(m1[4],m1[3]-1,m1[2]);
            var ed = new Date(m2[4],m2[3]-1,m2[2]);

            return (ed.getTime() - sd.getTime())/1000.0/3600.0/24.0;
        }

        function dateSelected(cal)
        {

            var period = findDayPeriodFromDTString('<%= startD %>','<%= endD %>');


            if (! cal.dateClicked)
            {
                return;
            }

            var d = cal.date;
            d.setHours(0);
            d.setMinutes(0);
            d.setSeconds(0);

            var form = $('dateSelect<%= prevNextNo %>')

            form['sDay'].value = d.getDate();
            form['sMonth'].value = d.getMonth() + 1;
            form['sYear'].value = d.getFullYear();

            var d2 = new Date(d.getTime() + period*3600*24*1000);

            form['eDay'].value = d2.getDate();
            form['eMonth'].value = d2.getMonth() + 1;
            form['eYear'].value = d2.getFullYear();

            form.submit()

        }
    <% end %>

    var cal = Calendar.setup({
        button: 'selectDateIcon<%= prevNextNo %>',
        eventName: "click",
        ifFormat: "%d/%m/%Y",
        showsTime: false,
        firstDay: 1,
        onSelect : dateSelected
        });
    </script>

<% end %>
