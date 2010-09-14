<span id="<%= name %>DatePlace"></span>
<input type="hidden" value="<%= date.day %>" name="<%= name %>Day" id="<%= name %>Day"/>
<input type="hidden" value="<%= date.month %>" name="<%= name %>Month" id="<%= name %>Month"/>
<input type="hidden" value="<%= date.year %>" name="<%= name %>Year" id="<%= name %>Year"/>
<input type="hidden" value="<%= date.hour %>" name="<%= name %>Hour" id="<%= name %>Hour" />
<input type="hidden" value="<%= date.minute %>" name="<%= name %>Min" id="<%= name %>Min" />
<script type="text/javascript">
IndicoUI.executeOnLoad(function() {
    var format = '<%= format %>';
    <% if withTime: %>
        var <%= name %>Date = IndicoUI.Widgets.Generic.dateField(true, null, ['<%= name %>Day', '<%= name %>Month', '<%= name %>Year', '<%= name %>Hour', '<%= name %>Min'], null, format);
    <% end %>
    <% else: %>
        var <%= name %>Date = IndicoUI.Widgets.Generic.dateField(false, null, ['<%= name %>Day', '<%= name %>Month', '<%= name %>Year', '<%= name %>Hour', '<%= name %>Min'], null, format);
    <% end %>
    $E('<%= name %>DatePlace').set(<%= name %>Date);
    <%= name %>Date.set('<%= dateDisplay %>');
});
</script>
