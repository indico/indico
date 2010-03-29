<?xml version='1.0'?>
<!-- $Id: standardMeetingEventBody.xsl,v 1.5 2009/06/16 14:59:27 eragners Exp $

     This file is part of CDS Indico.
     Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.

     CDS Indico is free software; you can redistribute it and/or
     modify it under the terms of the GNU General Public License as
     published by the Free Software Foundation; either version 2 of the
     License, or (at your option) any later version.

     CDS Indico is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
     59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
     -->
<xsl:stylesheet version='1.0'
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template name="meetingEventBody">
    <xsl:param name="minutes"/>
    <div class="meetingEventSubHeader">

      <xsl:call-template name="header2"><xsl:with-param name="minutes" select="$minutes"/></xsl:call-template>

    </div>

    <div class="meetingEventBody">

        <div style="position: absolute; right: 50px; top: 3px;"><span class="fakeLink dropDownMenu" id="goToDayLink"><strong>Go to day</strong></span></div>

<script type="text/javascript">

<![CDATA[
var goToDayMenuItems = {};
]]>

<xsl:for-each select="./session|./contribution|./break">
    <xsl:variable name="day" select="substring(./startDate,0,11)"/>
    <xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
        goToDayMenuItems['<xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template>'] = '#<xsl:value-of select="$day"/>';
    </xsl:if>
</xsl:for-each>


 <xsl:text disable-output-escaping="yes"><![CDATA[
var goToDayLink = $E('goToDayLink');
var goToDayMenu = null;

if (keys(goToDayMenuItems).length < 2) {
        goToDayLink.dom.style.display = 'none';
}

goToDayLink.observeClick(function(e) {
    // Close the menu if clicking the link when menu is open
    if (goToDayMenu != null && goToDayMenu.isOpen()) {
        goToDayMenu.close();
        goToDayMenu = null;
        return;
    }

    // build a dictionary that represents the menu

    goToDayMenu = new PopupMenu(goToDayMenuItems, [goToDayLink], null, true, true);
    var pos = goToDayLink.getAbsolutePosition();
    goToDayMenu.open(pos.x + goToDayLink.dom.offsetWidth + 10, pos.y + goToDayLink.dom.offsetHeight + 3);

    return false;
});
]]>
</xsl:text>

</script>

        <xsl:call-template name="body"><xsl:with-param name="minutes" select="$minutes"/></xsl:call-template>
    </div>

</xsl:template>

</xsl:stylesheet>
