<textarea
    id="{{ getName(field.input) }}"
    name="{{ getName(field.input) }}"
    cols="{{ field.values.numberOfColumns }}"
    rows="{{ field.values.numberOfRows }}"
    ng-required="field.mandatory"
    ng-disabled="!hasPlacesLeft(field)"></textarea>

<span class="inputDescription">
    {{ field.description }}
</span>
