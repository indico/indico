% if not rb_active:
    <p>
        <strong style="font-size: 1.2em; color: #f00;">
            ${ _('The Room Booking system is currently DISABLED in indico.conf') }
        </strong>
    </p>
% endif

<%include file="ErrorList.tpl" args='errors=form.error_list, msg=_("There are some errors:")'/>

<form method="post" action="">
    ${ form.csrf_token() }
    <table>
        % for field in form.visible_fields:
            <tr>
                <td style="text-align: right; vertical-align: top;">${ field.label() }</td>
                <td>${ field(**field_opts.get(field.short_name, {})) }</td>
            </tr>
        % endfor
    </table>
    <input class="i-button" type="submit" value="${ _('Save') }">
</form>
