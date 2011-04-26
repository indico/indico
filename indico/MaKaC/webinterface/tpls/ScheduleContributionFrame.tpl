<div style="overflow: visible; border: 1px solid #DDDDDD; padding: 10px; height: 20px; margin-left: auto; margin-right: auto;">

        <div style="float: left;">
            <span style="float: left; margin-right: 5px;">Contribution:</span>
            <form action="${ handler.getURL(self_._conf) }" method="GET">
                <select name="contribId" onchange="javascript: this.form.submit();">
                    % for contrib in contribList:
                        <option value="${ contrib.getId() }"
                            % if self_._contrib == contrib:
                                selected
                            % endif
>
                            ${ contrib.getTitle() }
                        </option>
                   % endfor
                </select>
                <input type="hidden" name="day" value="${ days }" />
                <input type="hidden" name="confId" value="${ self_._conf.getId() }" />
           </form>
        </div>
        <div style="float: left; padding-left: 50px;">
            <form action="${ urlHandlers.UHContribModifSchedule.getURL(self_._contrib) }" method="POST" style="display: inline;">
                <input type="hidden" name="day" value="${ days }" />
                <input type="submit" class="btn" value="Timetable" />
            </form>
        </div>
    </div>

${ body }
