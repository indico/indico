<%inherit file="ConfModifBadgeDesign.tpl"/>

<%block name="defaults">
    var zoom_factor = 0.5;
    var TPL_DEFAULT_SIZE = [525, 742];
    var numeric_mode = true;
</%block>


<%block name="font_sizes">
    <option>160pt</option>
    <option>150pt</option>
    <option>140pt</option>
    <option>130pt</option>
    <option>120pt</option>
    <option>110pt</option>
    <option>100pt</option>
    <option>90pt</option>
    <option>80pt</option>
    <option>70pt</option>
    <option>60pt</option>
    <option>50pt</option>
    <option>40pt</option>
    <option selected>30pt</option>
    <option>20pt</option>
    <option>15pt</option>
    <option>12pt</option>
    <option>10pt</option>
    <option>8pt</option>
</%block>

<%block name="background_options">
    <div>
        <label>${_("Stretch")}</label>
        <input checked type="radio" id="bgPosStretch" name='bgPosition' value="Stretch" />
        <label>${_("Center")}</label>
        <input type='radio' id="bgPosCenter" name='bgPosition' value="Center" />
    </div>
</%block>