<?xml version='1.0'?>
<!--

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

<xsl:include href="include/date.xsl"/>
<xsl:include href="include/common.xsl"/>
<xsl:include href="include/indico.xsl"/>
<xsl:include href="include/standardMeetingEventBody.xsl"/>
<xsl:output method="html"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">

	<div class="eventWrapper">

<div class="meetingEventHeader">
	<h1>
		<xsl:text disable-output-escaping="yes"></xsl:text><xsl:value-of select="./title" disable-output-escaping="yes"/><xsl:text disable-output-escaping="yes"></xsl:text>
	</h1>
	<xsl:if test="count(child::chair) != 0">
    	<span class="chairedBy">
			chaired by <xsl:apply-templates select="./chair"/>
		</span>
    </xsl:if>
    <div class="details">



        <xsl:choose>
        <xsl:when test="substring(./startDate,0,11) = substring(./endDate,0,11)">
            <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,21)"/>
            </xsl:call-template>
            from <strong><xsl:value-of select="substring(./startDate,12,5)"/></strong>
            to <strong><xsl:value-of select="substring(./endDate,12,5)"/></strong>
        </xsl:when>
        <xsl:otherwise>
            from
            <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
            </xsl:call-template>
            at <strong><xsl:value-of select="substring(./startDate,12,5)"/></strong>
            to
            <xsl:call-template name="prettydate">
            <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
            </xsl:call-template>
            at <strong><xsl:value-of select="substring(./endDate,12,5)"/></strong>
        </xsl:otherwise>
        </xsl:choose>
        (<xsl:value-of select="substring(./timezone,0,25)"/>)

        <xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
            <br />at <strong><xsl:apply-templates select="./location"><xsl:with-param name="span">headerRoomLink</xsl:with-param></xsl:apply-templates></strong>
        </xsl:if>
    </div>

    <xsl:call-template name="displayModifIcons">
      <xsl:with-param name="item" select="."/>
      <xsl:with-param name="confId" select="/iconf/ID"/>
      <xsl:with-param name="sessId" value=""/>
      <xsl:with-param name="contId" value=""/>
      <xsl:with-param name="subContId" value=""/>
      <xsl:with-param name="alignMenuRight">true</xsl:with-param>
      <xsl:with-param name="manageLink">true</xsl:with-param>
      <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
    </xsl:call-template>


</div>

	    <xsl:call-template name="meetingEventBody"><xsl:with-param name="minutes">off</xsl:with-param></xsl:call-template>

</div>
</xsl:template>

</xsl:stylesheet>

