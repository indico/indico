<span id="${ name }DatePlace"></span>

% if date:
<input type="hidden" value="${ date.day }" name="${ name }Day" id="${ name }Day"/>
<input type="hidden" value="${ date.month }" name="${ name }Month" id="${ name }Month"/>
<input type="hidden" value="${ date.year }" name="${ name }Year" id="${ name }Year"/>
<input type="hidden" value="${ date.hour }" name="${ name }Hour" id="${ name }Hour" />
<input type="hidden" value="${ date.minute }" name="${ name }Min" id="${ name }Min" />
% else:
<input type="hidden" value="" name="${ name }Day" id="${ name }Day"/>
<input type="hidden" value="" name="${ name }Month" id="${ name }Month"/>
<input type="hidden" value="" name="${ name }Year" id="${ name }Year"/>
<input type="hidden" value="" name="${ name }Hour" id="${ name }Hour" />
<input type="hidden" value="" name="${ name }Min" id="${ name }Min" />
% endif

<script type="text/javascript">
IndicoUI.executeOnLoad(function() {
    var format = '${ format }';

    <% wtime = jsBoolean(not withTime) %>
    <% mandatory = jsBoolean(isMandatory) %>

    var ${ name }Date = new DateTimeSelectorWFields({}, format,
        ${ mandatory }, ${ wtime },
        ['${ name }Day', '${ name }Month', '${ name }Year',
         '${ name }Hour', '${ name }Min']);

    $E('${ name }DatePlace').set(${ name }Date.draw());
    ${ name }Date.plugParameterManager(parameterManager);

    ${ name }Date.set('${ dateDisplay }', true);


});
</script>
