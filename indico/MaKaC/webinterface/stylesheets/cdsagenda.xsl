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
<xsl:include href="include/agenda.xsl"/>
<xsl:output method="html"/>

<!-- Global object: Agenda -->
<xsl:template match="iconf">

<table width="99%" border="0" cellpadding="0" cellspacing="0">
<tr>
  <td>
  <xsl:call-template name="header"/>

<xsl:for-each select="./session|./contribution|./break">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
	<a name="{$day}"/>
	<br/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><br/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><b>
	<xsl:call-template name="prettydate">
		<xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
	</xsl:call-template>
	</b>
	<hr/>
</xsl:if>
<xsl:if test="name(.)='contribution' or name(.)='break'">
<xsl:text disable-output-escaping="yes">
&#60;table width="100%" cellpadding="4" cellspacing="0" border="0"&#62;
</xsl:text>
</xsl:if>
<xsl:apply-templates select="."/>
<xsl:if test="name(.)='contribution' or name(.)='break'">
<xsl:text disable-output-escaping="yes">
&#60;/table&#62;
</xsl:text>
</xsl:if>
</xsl:for-each>
  </td>
</tr>
</table>
</xsl:template>



<xsl:template match="session">
<xsl:variable name="ids" select="./ID"/>
<a name="{./ID}"/>
<table width="100%" cellpadding="1" cellspacing="0" border="0">
<tr class="headerselected" bgcolor="#000060">
  <td valign="top" class="headerselected" align="left">

    <font color="white">
    <b>
    <font size="+1" face="arial" color="white">
    <xsl:value-of select="./title" disable-output-escaping="yes"/>	
    </font>
    </b>
    </font>
    <font size="-2">
    (<xsl:value-of select="substring(./startDate,12,5)"/>
    -&gt;<xsl:value-of select="substring(./endDate,12,5)"/>)
    </font>
  </td>
  <td valign="top" align="right">
    <xsl:choose>
    <xsl:when test="./description != '' or count(child::convener) != 0 or count(child::material) != 0 or count(child::location) != 0">
    <table bgcolor="#f0c060" cellpadding="0" cellspacing="0" border="0" class="results">
    <xsl:if test="./description != ''">
    <tr>
      <td valign="top" colspan="2" width="400"  style="text-align: justify">
        <i><small><xsl:apply-templates select="./description"/></small></i>
      </td>
    </tr>
    </xsl:if>
    <xsl:if test="count(child::convener) != 0">
    <tr>
      <td valign="top">
        <b><strong>
        Chairperson:
        </strong></b>
      </td> 
      <td>
        <small>
        <xsl:apply-templates select="./convener"/>
        </small>
      </td>
    </tr>
    </xsl:if>
    <xsl:if test="count(child::location) != 0 and  (./location/name != ../location/name or ./location/room != ../location/room)">
    <tr>
      <td valign="top">
        <b><strong>
        Location:
        </strong></b>
      </td>
      <td>
        <small>
        <xsl:apply-templates select="./location"/>
        </small>
      </td>
    </tr>
    </xsl:if>
    <xsl:if test="count(child::material) != 0">
    <tr>
      <td valign="top">
        <b><strong>
        Material:
        </strong></b>
      </td>
      <td>
        <small>
        <xsl:for-each select="./material">
        <xsl:apply-templates select="."><xsl:with-param name="sessionId" select="../ID"/></xsl:apply-templates>
        </xsl:for-each>
        </small>
      </td>
    </tr>
    </xsl:if>
    <xsl:if test="@broadcasturl != ''">
    <tr>
      <td valign="top">
        <b><strong>
          Broadcast:
        </strong></b>
      </td>
      <td>
        <small>
        <a href="{@broadcasturl}">
        <img src="images/camera.gif" alt="" border="0" width="33" height="24"/>
        </a>
        </small>
      </td>
    </tr>
    </xsl:if>
    </table>
    </xsl:when>
    <xsl:otherwise>
    <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
    </xsl:otherwise>
    </xsl:choose>
  </td>
  <td style="padding-right:4px; width:23px">
    <xsl:call-template name="displayModifIcons">
      <xsl:with-param name="alignMenuRight">true</xsl:with-param>
      <xsl:with-param name="item" select="."/>
      <xsl:with-param name="confId" select="../ID"/>
      <xsl:with-param name="sessId" select="./ID"/>
      <xsl:with-param name="contId">null</xsl:with-param>
      <xsl:with-param name="subContId">null</xsl:with-param>
      <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.session</xsl:with-param>
    </xsl:call-template>
  </td>
</tr>
</table>
<xsl:if test="count(./contribution|./break) != 0">
<table width="100%" cellpadding="4" cellspacing="0" border="0">
<xsl:for-each select="./contribution|./break">
	<xsl:apply-templates select="."/>
</xsl:for-each>
</table>
</xsl:if>
<br/>
</xsl:template>



<xsl:template match="contribution">
<xsl:variable name="idt" select="./ID"/>
<tr>
  <td valign="top" width="1%">
    <font color="black">
    <b><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
    <xsl:value-of select="substring(./startDate,12,5)"/> 
    </b>
    </font>
    <xsl:if test="@broadcasturl != ''">
    <br/><a href="{@broadcasturl}">
    <img src="images/camera.gif" border="0" width="33" height="24"/>
    <br/>(video broadcast)</a>
    </xsl:if>
  </td>
  <xsl:choose>
  <xsl:when test="(./location/name != ../location/name and ./location/name != '') or (./location/room != ../location/room and ./location/room != '' and ./location/room != '0--')">
  <td align="center" valign="top" class="header" width="1%">
    <xsl:apply-templates select="./location"/>
  </td>
  </xsl:when>
  <xsl:otherwise>
    <td width="1%" align="center" valign="top"></td>
  </xsl:otherwise>
  </xsl:choose>
  <xsl:choose>
  <xsl:when test="count(preceding-sibling::contribution) mod 2 = 1">
  <xsl:text disable-output-escaping="yes">
  &#60;td colspan="2" width="75%" valign="top" bgcolor="#E4E4E4"&#62;
    &#60;table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#E4E4E4"&#62;
  </xsl:text>
  </xsl:when>
  <xsl:otherwise>
  <xsl:text disable-output-escaping="yes">
  &#60;td colspan="2" width="75%" valign="top" bgcolor="#F6F6F6"&#62;
    &#60;table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#F6F6F6"&#62;
  </xsl:text>
  </xsl:otherwise>
  </xsl:choose>
    <tr>
      <td valign="top" align="left">
        <font class="headline"><b>
        <xsl:value-of select="./title" disable-output-escaping="yes"/>
        </b></font> 
        <xsl:if test="./duration != '00:00'"><small><font color="red"> (<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>) </font></small></xsl:if>
        <xsl:if test="count(child::repno) != 0">(
		<xsl:for-each select="./repno">
			<xsl:apply-templates select="."/> 
            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		</xsl:for-each>
        )</xsl:if>
        <xsl:if test="count(child::material) != 0">
        (<xsl:for-each select="./material">
        <xsl:apply-templates select="."><xsl:with-param name="contribId" select="../ID"/></xsl:apply-templates>
        <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
        </xsl:for-each>) 
        </xsl:if>
      </td>
      <td align="right">
        <xsl:if test="count(child::speakers) != 0">
        <xsl:apply-templates select="./speakers"/>
        </xsl:if>
      </td>
      <td>
        <xsl:if test="name(..) = 'session'">
        <xsl:call-template name="displayModifIcons">        
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../../ID"/>
          <xsl:with-param name="sessId" select="../ID"/>
          <xsl:with-param name="contId" select="./ID" />
          <xsl:with-param name="subContId">null</xsl:with-param>
          <xsl:with-param name="alignMenuRight">true</xsl:with-param>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>
          </xsl:if>
          <xsl:if test="name(..) != 'session'">
        <xsl:call-template name="displayModifIcons">        
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../ID"/>
          <xsl:with-param name="sessId">null</xsl:with-param>
          <xsl:with-param name="contId" select="./ID" />
          <xsl:with-param name="subContId">null</xsl:with-param>
          <xsl:with-param name="alignMenuRight">true</xsl:with-param>
          <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>
        </xsl:if>
      </td>
    </tr>	
    <xsl:if test="./abstract != ''">
    <tr>
      <td colspan="3" style="text-align: justify">
        <xsl:apply-templates select="./abstract"/>
      </td>
    </tr>
    </xsl:if>
    <xsl:for-each select="subcontribution">
      <xsl:apply-templates select="."/>
    </xsl:for-each>
    <xsl:text disable-output-escaping="yes">
    &#60;/table&#62;
  &#60;/td&#62;
    </xsl:text>
</tr>
</xsl:template>


<xsl:template match="subcontribution">
	<xsl:variable name="idt" select="./ID"/>
	<tr>
		<td align="left">
		<ul>
		<li>
		<b class="headline"><small>
		<xsl:value-of select="./title" disable-output-escaping="yes"/>
		</small></b>
		<xsl:if test="./duration != '00:00'">
			<small><font color="red"> (<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>) </font></small>
		</xsl:if>
		<font color="black">
        <xsl:if test="count(child::repno) != 0">(
		<xsl:for-each select="./repno">
			<xsl:apply-templates select="."/> 
            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		</xsl:for-each>
        )</xsl:if>
		<xsl:if test="count(child::material) != 0">
			(<xsl:for-each select="./material">
			<xsl:apply-templates select="."><xsl:with-param name="contribId" select="../../ID"/><xsl:with-param name="subContId" select="../ID"/></xsl:apply-templates>
			<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
			</xsl:for-each>)
		</xsl:if>
		<xsl:if test="./abstract != ''">
			<br/><small><xsl:apply-templates select="./abstract"/></small>
		</xsl:if>
		</font>
		</li>
		</ul>

		</td>
		<td align="right">
		<xsl:if test="count(child::speakers) != 0">
			<xsl:apply-templates select="./speakers"/>
		</xsl:if>
		</td>
        <td>
        <xsl:if test="name(../..) = 'session'">
            <xsl:call-template name="displayModifIcons">        
              <xsl:with-param name="item" select="."/>
              <xsl:with-param name="confId" select="../../../ID"/>
              <xsl:with-param name="sessId" select="../../ID"/>
              <xsl:with-param name="contId" select="../ID" />
              <xsl:with-param name="subContId" select="./ID"/>
              <xsl:with-param name="alignMenuRight">true</xsl:with-param>
              <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
            </xsl:call-template>
              </xsl:if>
              <xsl:if test="name(../..) != 'session'">
            <xsl:call-template name="displayModifIcons">        
              <xsl:with-param name="item" select="."/>
              <xsl:with-param name="confId" select="../../ID"/>
              <xsl:with-param name="sessId">null</xsl:with-param>
              <xsl:with-param name="contId" select="../ID" />
              <xsl:with-param name="subContId" select="./ID"/>
              <xsl:with-param name="alignMenuRight">true</xsl:with-param>
              <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
            </xsl:call-template>
            </xsl:if>
        </td>
	</tr>
</xsl:template>


<xsl:template match="break">
<tr class="header">
	<td align="center" valign="top" width="1%">
		<font color="black">
		<b><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:value-of select="substring(./startDate,12,5)"/> 
		</b>
		</font>
	</td>
	<td colspan="3">

                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                </xsl:call-template>

		<xsl:value-of select="./name" disable-output-escaping="yes"/>
        <xsl:if test="./duration != '00:00'"><small><font color="red"> (<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>) </font></small></xsl:if>
	</td>
</tr>
</xsl:template>


<xsl:template match="chair|announcer|convener">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span"></xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling::user) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>


<xsl:template match="convener|speakers">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span"></xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling::user) != 0">,<xsl:text disable-output-escaping="yes"> </xsl:text></xsl:if>
	</xsl:for-each>
</xsl:template>


</xsl:stylesheet>
