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

<xsl:output method="html"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">

<a name="top"/>
<table>
<tr>
<td>

<xsl:call-template name="displayModifIcons">
    <xsl:with-param name="item" select="."/>
    <xsl:with-param name="confId" select="/iconf/ID"/>
    <xsl:with-param name="sessId" value=""/>
    <xsl:with-param name="sessCode" value=""/>
    <xsl:with-param name="contId" value=""/>
    <xsl:with-param name="subContId" value=""/>
    <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
</xsl:call-template>

<span class="title1Green">
<xsl:value-of select="./title" disable-output-escaping="yes"/>
</span>
<xsl:if test="./repno!=''">
	/ <xsl:value-of select="./repno" disable-output-escaping="yes"/>
</xsl:if>
<xsl:if test="count(./material) != 0">
(
  <xsl:for-each select="./material">
    <xsl:apply-templates select="."/>
  </xsl:for-each>
)
</xsl:if>
	<br/><br/>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	Description :
        <xsl:apply-templates select="./description"/>
	</span>

<xsl:if test="./participants != ''">
	<br/>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
		Participants: <xsl:value-of select="./participants" disable-output-escaping="yes"/>
	</span>
</xsl:if>

<xsl:if test="count(./videoconference) != 0">
	<br/>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
          Videoconference:
          <xsl:for-each select="./videoconference">
            <xsl:apply-templates select="."/>
          </xsl:for-each>
	</span>
</xsl:if>

<xsl:if test="count(./audioconference) != 0">
	<br/>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
          Audioconference:
          <xsl:for-each select="./audioconference">
            <xsl:apply-templates select="."/>
          </xsl:for-each>
	</span>
</xsl:if>

</td>
</tr>
</table>
<br/>
<center>
<table>
<tr>
<td>
<b>Programme:</b>
<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
<font size="-3">
  <xsl:for-each select="./session|./contribution|./break">
    <xsl:variable name="day" select="substring(./startDate,0,11)"/>
    <xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
    <small><a href="#{$day}"><xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template></a>
    |
    </small>
    </xsl:if>
  </xsl:for-each>
</font>
</td>
</tr>
<tr>
<td>
<xsl:if test="count(child::chair) != 0">
  <b>Chaired by:</b>
  <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
  <xsl:apply-templates select="./chair"/>
</xsl:if>
</td>
</tr>
</table>

<xsl:for-each select="./session|./contribution|./break">
 <xsl:variable name="day" select="substring(./startDate,0,11)"/>
 <xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
	<br/>
	<a name="{$day}"/>
	<table width="95%" border="0" cellspacing="0" cellpadding="0" style="border: medium none ; border-collapse: collapse;">
	<tr>
		<td width="679" colspan="7" valign="top" style="border-style: solid; border-color: #669999; border-width: 1.5pt 1.5pt 1pt; padding: 0cm 5.4pt; background: #669999 none repeat scroll 0%; -moz-background-clip: initial; -moz-background-inline-policy: initial; -moz-background-origin: initial;">
		<p class="MsoNormal" align="center" style="margin-top: 3pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 10pt; font-family: Arial; color: white;">
		<b>
		<xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template>
		</b>
		</span>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<a href="#top">
		<span lang="EN-GB" style="font-size: 10pt; font-family: Arial; color: white;">
            top<img src="images/upArrow.png" border="0" style="vertical-align:middle" alt="top"/>
		</span>
		</a>
		</p>
		</td>
	</tr>
	<tr>
		<td width="43" valign="top" style="border-style: none solid solid; border-width: medium 1pt 1pt 1.5pt; border-left: 1.5pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin: 3pt -2.85pt 1e-04pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">Time</span></p></td>

<xsl:if test="count(../session[substring(./startDate,0,11)=$day]) > 0">
		<td width="36" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin: 3pt -2.85pt 1e-04pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">Organizer</span></p></td>
		<td width="168" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin-top: 3pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">Theme</span></p></td>
</xsl:if>

		<td width="204" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin-top: 3pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">Topic</span></p></td>
		<td width="144" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin: 3pt -5.4pt 1e-04pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">CERN
		speakers / participants</span></p></td>
		<td width="24" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin: 3pt -2.85pt 1e-04pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">Min</span></p></td>
		<td width="60" valign="top" style="border-style: none solid solid none; border-width: medium 1.5pt 1pt medium; border-right: 1.5pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
		<p class="MsoNormal" align="center" style="margin: 3pt -2.85pt 1e-04pt; text-align: center;">
		<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">Place</span></p></td>
	</tr>
	<xsl:for-each select="../session[substring(./startDate,0,11)=$day]|../contribution[substring(./startDate,0,11)=$day]|../break[substring(./startDate,0,11)=$day]">
	<xsl:apply-templates select="."/>
	</xsl:for-each>
	</table>
 </xsl:if>
</xsl:for-each>

</center>
<br/>
<br/>
</xsl:template>














<xsl:template match="session">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<xsl:variable name="nbcontributions" select="count(descendant::contribution)+count(descendant::break)+count(descendant::subcontribution)+1"/>
<tr>
	<td rowspan="{$nbcontributions}" valign="top" style="border-style: none solid solid; border-width: medium 1pt 1pt 1.5pt; border-left: 1.5pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<xsl:if test="substring(./startDate,12,5) != '00:00'"><xsl:value-of select="substring(./startDate,12,5)"/></xsl:if>
	<xsl:if test="substring(./endDate,12,5) != '00:00'">-<xsl:value-of select="substring(./endDate,12,5)"/></xsl:if>
	</span>
	</td>
	<td rowspan="{$nbcontributions}" valign="top" style="border-style: none solid solid; border-width: medium 1pt 1pt 1.5pt; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<xsl:if test="count(child::convener) != 0">
		<xsl:apply-templates select="./convener"/>
	</xsl:if>
	</span>
	</td>

	<xsl:if test="count(../session[substring(./startDate,0,11)=$day]) > 1">
        <!--<td width="36" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>-->
		<td width="168" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
	</xsl:if>

	<td rowspan="{$nbcontributions}" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<a name="{./ID}"/>
	<xsl:variable name="ids" select="./ID"/>

      <xsl:call-template name="displayModifIcons">
        <xsl:with-param name="item" select="."/>
        <xsl:with-param name="confId" select="../ID"/>
        <xsl:with-param name="sessId" select="./ID"/>
        <xsl:with-param name="sessCode" select="./code"/>
        <xsl:with-param name="contId">null</xsl:with-param>
        <xsl:with-param name="subContId">null</xsl:with-param>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.session</xsl:with-param>
      </xsl:call-template>

	<xsl:value-of select="./title" disable-output-escaping="yes"/>
	<xsl:if test="count(./material) != 0">
	(
	  <xsl:for-each select="./material">
	    <xsl:apply-templates select="."><xsl:with-param name="sessionId" select="../ID"/></xsl:apply-templates>
	  </xsl:for-each>
	)
	</xsl:if>
	</span>
	<br/>
	<xsl:if test="./abstract != ''">
        <p lang="EN-GB" style="font-size: 8pt; font-family: Arial; margin-left: 14px;"><xsl:apply-templates select="./abstract"/></p>
	</xsl:if>
    </td>
    <td valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
	<xsl:choose>
	<xsl:when test="count(contribution)=0">
	<td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
    <!--<td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
    <td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>-->
	</xsl:when>
	<xsl:otherwise>
	<td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 0pt dotted #669999; padding: 0cm 5.4pt;"></td>
    <!--<td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 0pt dotted #669999; padding: 0cm 5.4pt;"></td>
    <td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 0pt dotted #669999; padding: 0cm 5.4pt;"></td>-->
	</xsl:otherwise>
	</xsl:choose>

	<td rowspan="{$nbcontributions}" valign="top" style="border-style: none solid solid none; border-width: medium 1.5pt 1pt medium; border-right: 1.5pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
		<xsl:apply-templates select="./location"/>
	</xsl:if>
	</span>
	</td>
</tr>
<xsl:for-each select="./contribution|./break">
<xsl:apply-templates select="."/>
</xsl:for-each>
</xsl:template>




<xsl:template match="contribution">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<xsl:variable name="nbsubcontributions" select="count(./subcontribution)+1"/>
<xsl:if test="count(../../session)=0">
<tr>
	<td rowspan="{$nbsubcontributions}" valign="top" class="timecolumn">
	<span class="smallfont">
	<xsl:if test="substring(./startDate,12,5) != '00:00'"><xsl:value-of select="substring(./startDate,12,5)"/></xsl:if>
	<xsl:if test="substring(./endDate,12,5) != '00:00'">-<xsl:value-of select="substring(./endDate,12,5)"/></xsl:if>
	</span>
	</td>

	<td width="36" valign="top" class="orgcolumn" rowspan="{$nbsubcontributions}"></td>

	<xsl:choose>
	<xsl:when test="count(./subcontribution)=0">
	<xsl:text disable-output-escaping="yes">&#60;td valign="top" class="topiccolumnnormal"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td valign="top" class="topiccolumnwithsc"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span class="smallfont">
	<a name="{./ID}"/>
	<xsl:variable name="idt" select="./ID"/>

        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../ID"/>
          <xsl:with-param name="sessId">null</xsl:with-param>
          <xsl:with-param name="sessCode">null</xsl:with-param>
          <xsl:with-param name="contId" select="./ID" />
          <xsl:with-param name="subContId">null</xsl:with-param>
          <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>

	<xsl:value-of select="./title" disable-output-escaping="yes"/>
	<xsl:if test="count(./material) != 0">
	(
	  <xsl:for-each select="./material">
	    <xsl:apply-templates select="."><xsl:with-param name="contribId" select="../ID"/></xsl:apply-templates>
	  </xsl:for-each>
	)
	</xsl:if>
	</span>
	<br/>
	<xsl:if test="./abstract != ''">
        <p lang="EN-GB" style="font-size: 8pt; font-family: Arial; margin-left: 14px;"><xsl:apply-templates select="./abstract"/></p>
	</xsl:if>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

    <td width="204" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;" rowspan="{$nbsubcontributions}"></td>

	<xsl:choose>
	<xsl:when test="count(subcontribution)=0">
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" class="spkcolumnnormal"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" class="spkcolumnwithsc"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span class="smallfont">
	<xsl:if test="count(child::speakers) != 0">
		<xsl:apply-templates select="./speakers"/>
	</xsl:if>
	</span>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

	<xsl:choose>
	<xsl:when test="count(subcontribution)=0">
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" class="durcolumnnormal"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" class="durcolumnwithsc"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span class="smallfont">
		<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>
	</span>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

	<td rowspan="{$nbsubcontributions}" valign="top" style="border-style: none solid solid none; border-width: medium 1.5pt 1pt medium; border-right: 1.5pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;">
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
		<xsl:apply-templates select="./location"/>
	</xsl:if>
	</span>
	</td>
</tr>
</xsl:if>
<xsl:if test="count(../../session)>0">
<tr>
	<xsl:if test="count(../session[substring(./startDate,0,11)=$day]) > 1">
		<td width="36" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
		<td width="168" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
	</xsl:if>

	<xsl:choose>
	<xsl:when test="count(./subcontribution)=0">
	<xsl:text disable-output-escaping="yes">&#60;td valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt dotted #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<a name="{./ID}"/>
	<xsl:variable name="idt" select="./ID"/>

        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../../ID"/>
          <xsl:with-param name="sessId" select="../ID"/>
          <xsl:with-param name="sessCode" select="../code"/>
          <xsl:with-param name="contId" select="./ID" />
          <xsl:with-param name="subContId">null</xsl:with-param>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>

	<xsl:value-of select="./title" disable-output-escaping="yes"/>
	<xsl:if test="count(./material) != 0">
	(
	  <xsl:for-each select="./material">
	    <xsl:apply-templates select="."><xsl:with-param name="contribId" select="../ID"/></xsl:apply-templates>
	  </xsl:for-each>
	)
	</xsl:if>
	</span>
	<br/>
	<xsl:if test="./abstract != ''">
        <p lang="EN-GB" style="font-size: 8pt; font-family: Arial; margin-left: 14px;"><xsl:apply-templates select="./abstract"/></p>
	</xsl:if>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

	<xsl:choose>
	<xsl:when test="count(subcontribution)=0">
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt dotted #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<xsl:if test="count(child::speakers) != 0">
		<xsl:apply-templates select="./speakers"/>
	</xsl:if>
	</span>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

	<xsl:choose>
	<xsl:when test="count(subcontribution)=0">
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt dotted #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
		<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>
	</span>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

</tr>
</xsl:if>
<xsl:for-each select="./subcontribution">
<xsl:apply-templates select="."/>
</xsl:for-each>
</xsl:template>



<xsl:template match="subcontribution">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<tr>
	<xsl:choose>
	<xsl:when test="count(following-sibling::subcontribution) > 0">
	<xsl:text disable-output-escaping="yes">&#60;td valign="top" style="border-style: none dotted dotted none; border-width: medium 1pt 1pt medium; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt dotted #669999; padding: 0cm 5.4pt; padding-left: 30px;"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td valign="top" style="border-style: none dotted dotted none; border-width: medium 1pt 1pt medium; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt; padding-left: 30px;"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span class="smallfont">
	<a name="{./ID}"/>
	<xsl:variable name="idt" select="./ID"/>

    <xsl:if test="name(../..) = 'session'">
	<xsl:call-template name="displayModifIcons">
	  <xsl:with-param name="item" select="."/>
	  <xsl:with-param name="confId" select="../../../ID"/>
	  <xsl:with-param name="sessId" select="../../ID"/>
      <xsl:with-param name="sessCode" select="../../code"/>
	  <xsl:with-param name="contId" select="../ID" />
	  <xsl:with-param name="subContId" select="./ID"/>
	  <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
	</xsl:call-template>
      </xsl:if>
      <xsl:if test="name(../..) != 'session'">
	<xsl:call-template name="displayModifIcons">
	  <xsl:with-param name="item" select="."/>
	  <xsl:with-param name="confId" select="../../ID"/>
	  <xsl:with-param name="sessId">null</xsl:with-param>
      <xsl:with-param name="sessCode">null</xsl:with-param>
	  <xsl:with-param name="contId" select="../ID" />
	  <xsl:with-param name="subContId" select="./ID"/>
	  <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
	</xsl:call-template>
    </xsl:if>

	<xsl:value-of select="./title" disable-output-escaping="yes"/>
	<xsl:if test="count(./material) != 0">
	(
	  <xsl:for-each select="./material">
	    <xsl:apply-templates select="."><xsl:with-param name="contribId" select="../ID"/></xsl:apply-templates>
	  </xsl:for-each>
	)
	</xsl:if>
	</span>
	<br/>
	<xsl:if test="./abstract != ''">
        <p lang="EN-GB" style="font-size: 8pt; font-family: Arial; margin-left: 14px;"><xsl:apply-templates select="./abstract"/></p>
	</xsl:if>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

	<xsl:choose>
	<xsl:when test="count(following-sibling::subcontribution) > 0">
	<xsl:text disable-output-escaping="yes">&#60;td align="center" valign="top" style="border-style: none dotted dotted none; border-width: medium 1pt 1pt medium; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt dotted #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td align="center" valign="top" style="border-style: none dotted dotted none; border-width: medium 1pt 1pt medium; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
	<xsl:if test="count(child::speakers) != 0">
		<xsl:apply-templates select="./speakers"/>
	</xsl:if>
	</span>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

	<xsl:choose>
	<xsl:when test="count(following-sibling::subcontribution) > 0">
	<xsl:text disable-output-escaping="yes">&#60;td align="center"  valign="top" style="border-style: none dotted dotted none; border-width: medium 1pt 1pt medium; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt dotted #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	<xsl:text disable-output-escaping="yes">&#60;td align="center" valign="top" style="border-style: none dotted dotted none; border-width: medium 1pt 1pt medium; border-left: 1pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"&#62;</xsl:text>
	</xsl:otherwise>
	</xsl:choose>
	<span lang="EN-GB" style="font-size: 8pt; font-family: Arial;">
		<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>
	</span>
	<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>
</tr>
</xsl:template>


<xsl:template match="break">
    <tr>
        <xsl:if test="count(../../session)=0">
            <td width="43" valign="top" style="border-style: none solid solid; border-width: medium 1pt 1pt 1.5pt; border-left: 1.5pt solid #669999; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
            <td width="36" valign="top" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
        </xsl:if>
        <td colspan="3" align="center"  valign="top" bgcolor="lightblue" style="border-style: none solid solid none; border-width: medium 1pt 1pt medium; border-right: 1pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"><xsl:value-of select="./name"/></td>
        <td align="center" valign="top" style="border-style: none solid dotted none; border-width: medium 1pt 1pt medium; border-right: 1pt solid rgb(102, 153, 153); border-bottom: 1pt dotted rgb(102, 153, 153); padding: 0cm 5.4pt;">
            <span class="smallfont">
        		<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>
            </span>
        </td>
        <xsl:if test="count(../../session)=0">
            <td width="60" valign="top" style="border-style: none solid solid none; border-width: medium 1.5pt 1pt medium; border-right: 1.5pt solid #669999; border-bottom: 1pt solid #669999; padding: 0cm 5.4pt;"></td>
        </xsl:if>
    </tr>
</xsl:template>

<xsl:template match="chair|announcer">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span">author</xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>

<xsl:template match="convener|speakers">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span"></xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>

<xsl:template match="name">
	<xsl:value-of select="./@first" disable-output-escaping="yes"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="./@last" disable-output-escaping="yes"/>
</xsl:template>

<xsl:template match="location">
	<b><xsl:value-of select="./name"/></b>
	<xsl:if test="./room != '0--' and ./room != 'Select:'">
		(
		<xsl:value-of select="./room" disable-output-escaping="yes"/>
		)
	</xsl:if>
</xsl:template>


</xsl:stylesheet>
