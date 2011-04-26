<li class="UIPerson clearfix" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'" >

    % if not selectable:
        <input  type="image" style="padding: 3px;" class="UIRowButton"
                onclick="javascript:removeItem(${ id }, this.form);return false;"
                title="${ _("Remove this person from the list")}"
                src="${ systemIcon("remove") }" />
    % endif

    % if currentUserBasket:
        <% domId = id %>
        % if ParentPrincipalTableId:
            <% domId = "t" + str(ParentPrincipalTableId) + "av" + id %>
        % endif

        <span id="add_${ domId }_to_basket" class="UIRowButton" style="padding: 3px; height: 16px;"></span>
        <script type="text/javascript">
            $E('add_${ domId }_to_basket').set(new ToggleFavouriteButton(${ jsonEncode(avatar) }, {}, ${ jsBoolean(currentUserBasket.hasUserId(id)) }).draw());
        </script>
    % endif


    <span class="nameLink">

        % if selectable:
        <input type="${ inputType }" name="selectedPrincipals" value="${ id }" ${ selected }>
        % endif

        ${ fullName } <em>(${ email })</em>
    </span>

</li>
