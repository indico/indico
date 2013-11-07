<input type="number"
    id="{{ getName(field.input) }}"
    name="{{ getName(field.input) }}"
    value="{{ field.values.minValue }}"
    size="{{ field.values.length }}"
    min="{{ field.values.minValue }}"
    ng-class="{regFormIsBillable: el.isBillable}"
    ng-required="field.mandatory"
    ng-disabled="!hasPlacesLeft(field)"
    ng-change="change()"/>

<span class="regFormPrice">{{ field.price }}</span>
<span class="regFormCurrency"></span>
<span class="regFormSubtotal">{{ 'Total' | i18n }}:</span>
<span id="subtotal-{{ getName(field.input) }}">0</span>
<span class="regFormCurrency"></span>

<span class="inputDescription">
    {{ field.description }}
</span>
