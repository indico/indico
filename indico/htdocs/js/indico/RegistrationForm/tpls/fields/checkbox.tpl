<input type="checkbox"
    id="{{ name }}"
    name="{{ name }}"
    ng-class="{regFormIsBillable: el.isBillable}"
    ng-required="field.mandatory"
    ng-disabled="!hasPlacesLeft(field)"/>

<span ng-show="field.billable" class="regFormPrice">{{ field.price }}</span>
<span ng-show="field.billable" class="regFormCurrency"></span>

<!-- TODO use isDisabled() and isBillable() from ndRadioField with ng-show -->
{% if field.placesLimit != 0 and field.noPlacesLeft != 0 %}
    <span class="placesLeft">
        [{{field.noPlacesLeft}} {{ 'place(s) left' | i18n }}]
    </span>
{% elif field.placesLimit != 0 and field.noPlacesLeft == 0 %}
    <font color="red">
        ({{ 'no places left' | i18n }})
    </font>
{% endif %}

<span class="inputDescription">
    {{ field.description }}
</span>
