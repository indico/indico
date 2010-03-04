<?xml version='1.0'?>
<!-- $Id: agenda.xsl,v 1.4 2009/06/18 14:37:55 eragners Exp $

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

<xsl:template name="header">
<table width="100%" border="0" bgcolor="white" cellpadding="1" cellspacing="1">
<tr>
  <td valign="top" align="left">
    <table border="0" bgcolor="gray" cellspacing="1" cellpadding="1" width="100%">
    <tr>
      <td colspan="1">
    <table border="0" cellpadding="2" cellspacing="0" width="100%" class="headerselected" bgcolor="#000060">
    <tr>
          <td width="35">
            <img src="images/meeting.png" width="32" height="32" alt="lecture"/>
          </td>
          <td class="headerselected" align="right">
            <b><strong>
                <div style="float: left; height: 15px; width: 15px; padding-top: 7px;">
                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                    <xsl:with-param name="confId" select="./ID"/>
                    <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
                </xsl:call-template>
                </div>

            <font size="+2" face="arial" color="white">
            <xsl:value-of select="./title" disable-output-escaping="yes"/>
            </font>
            </strong></b>
            <small>
            <xsl:for-each select="./repno">
            <br/><xsl:apply-templates select="."/>
            </xsl:for-each>
            </small>
          </td>
        </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td>
        <table border="0" bgcolor="#f0c060" cellpadding="2" cellspacing="0" width="100%" >
        <tr>
          <td valign="top" align="right">
            <b><strong>
              Date/Time:
            </strong></b>
          </td>
          <td style="width:90%">
            <small>
            <xsl:choose>
            <xsl:when test="substring(./startDate,0,11) = substring(./endDate,0,11)">
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
              </xsl:call-template>
              <xsl:if test="substring(./startDate,12,5) != '00:00'">
                from <xsl:value-of select="substring(./startDate,12,5)"/>
              </xsl:if>
              <xsl:if test="substring(./endDate,12,5) != '00:00'">
                to <xsl:value-of select="substring(./endDate,12,5)"/>
                 (<xsl:value-of select="substring(./timezone,0,25)"/>)
              </xsl:if>
            </xsl:when>
            <xsl:otherwise>
              from
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
              </xsl:call-template>
              <xsl:if test="substring(./startDate,12,5) != '00:00'">
                (<xsl:value-of select="substring(./startDate,12,5)"/>)
              </xsl:if>
              to
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
              </xsl:call-template>
              <xsl:if test="substring(./endDate,12,5) != '00:00'">
                (<xsl:value-of select="substring(./endDate,12,5)"/>)
                 (<xsl:value-of select="substring(./timezone,0,25)"/>)
              </xsl:if>
            </xsl:otherwise>
            </xsl:choose>
            </small>
          </td>
        </tr>
        <xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
        <tr>
          <td valign="top" align="right">
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
        <xsl:if test="count(child::chair) != 0">
        <tr>
          <td valign="top" align="right">
            <b><strong>
            Chairperson:
            </strong></b>
          </td>
          <td>
            <small>
            <xsl:apply-templates select="./chair"/>
            </small>
          </td>
        </tr>
        </xsl:if>
        <xsl:if test="count(child::supportEmail) != 0">
        <tr>
          <td valign="top" align="right">
              <b><strong>
                  <xsl:value-of select="./supportEmail/@caption"/>
              </strong></b>
          </td>
          <td>
              <small>
                  <xsl:value-of select="./supportEmail"/>
             </small>
          </td>
        </tr>
        </xsl:if>
        <xsl:if test="./description != ''">
        <tr>
          <td valign="top" align="right">
            <b><strong>
            Description:
            </strong></b>
          </td>
          <td class="fixPreOverflow">
            <small>
            <xsl:apply-templates select="./description"/>
            </small>
          </td>
        </tr>
        </xsl:if>

        <xsl:if test="./participants != ''">
        <tr>
          <td valign="top" align="right">
            <b><strong>
            Participants:
            </strong></b>
          </td>
          <td>
            <i>
            <small>
            <xsl:value-of select="./participants" disable-output-escaping="yes"/>
            </small>
            </i>
          </td>
        </tr>
        </xsl:if>

        <xsl:if test="./apply != ''">
        <tr>
          <td valign="top" align="right"><b><strong>Want to participate:</strong></b></td>
          <td><i><small><a href="{./apply}">Apply here</a></small></i></td>
        </tr>
        </xsl:if>

        <xsl:if test="count(./videoconference) != 0">
        <tr>
          <td valign="top" align="right">
            <b><strong>
            Videoconference:
            </strong></b>
          </td>
          <td>
            <i>
            <small>
            <xsl:for-each select="./videoconference">
              <xsl:apply-templates select="."/>
            </xsl:for-each>
            </small>
            </i>
          </td>
        </tr>
        </xsl:if>
        <xsl:if test="count(./audioconference) != 0">
        <tr>
          <td valign="top" align="right">
            <b><strong>
            Audioconference:
            </strong></b>
          </td>
          <td>
            <i>
            <small>
            <xsl:for-each select="./audioconference">
              <xsl:apply-templates select="."/>
            </xsl:for-each>
            </small>
            </i>
          </td>
        </tr>
        </xsl:if>
        <xsl:if test="count(child::material) != 0">
        <tr>
          <td valign="top" align="right">
            <b><strong>
            Material:
            </strong></b>
          </td>
          <td>
            <xsl:for-each select="./material">
              <xsl:apply-templates select="."/>
            </xsl:for-each>
          </td>
        </tr>
        </xsl:if>
        </table>
      </td>
    </tr>
    </table>
  </td>
  <td align="right" valign="top">
    <table border="0" bgcolor="gray" cellspacing="1" cellpadding="1">
        <xsl:if test="count(child::session) != 0">
            <tr>
                <td>
                    <table bgcolor="white" cellpadding="2" cellspacing="0" border="0" width="100%">

                        <xsl:for-each select="session">
                            <tr>
                                <td valign="top" class="headerselected" bgcolor="#000060">
                                    <font size="-2" color="white">
                                        <xsl:choose>
                                        <xsl:when test="substring(./startDate,0,11) = substring(./endDate,0,11)">
                                            <xsl:call-template name="prettydate">
                                                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
                                            </xsl:call-template>
                                            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                                            <xsl:value-of select="substring(./startDate,12,5)"/>
                                            <xsl:if test="substring(./endDate,12,5) != '00:00'">-&gt;<xsl:value-of select="substring(./endDate,12,5)"/></xsl:if>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:call-template name="prettydate">
                                                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
                                            </xsl:call-template>
                                            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                                                <xsl:value-of select="substring(./startDate,12,5)"/>
                                                -&gt;
                                            <xsl:call-template name="prettydate">
                                                <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
                                            </xsl:call-template>
                                            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                                                <xsl:value-of select="substring(./endDate,12,5)"/>
                                        </xsl:otherwise>
                                        </xsl:choose>
                                    </font>
                                </td>
                    <xsl:choose>
            <xsl:when test="count(preceding-sibling::session) mod 2 = 1">
              <xsl:text disable-output-escaping="yes">
              &#60;td valign="top" bgcolor="#E4E4E4"&#62;
            </xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text disable-output-escaping="yes">
              &#60;td valign="top" bgcolor="#F6F6F6"&#62;
              </xsl:text>
            </xsl:otherwise>
            </xsl:choose>
              <a href="#{./ID}">
              <font size="-2">
              <xsl:choose>
              <xsl:when test="./title != ''">
                <xsl:value-of select="./title" disable-output-escaping="yes"/>
              </xsl:when>
              <xsl:otherwise>
                no title
              </xsl:otherwise>
              </xsl:choose>
              </font>
              </a>
              <font size="-2">
              <xsl:if test="count(child::location) != 0 and (./location/name != ../location/name or ./location/room != ../location/room)">
              (<xsl:apply-templates select="./location"/>)
              </xsl:if>
              </font>
              <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
        <xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>

        <xsl:choose>
        <xsl:when test="@chairperson != ''">
            <xsl:choose>
            <xsl:when test="count(preceding-sibling::session) mod 2 = 1">
                <xsl:text disable-output-escaping="yes">
            &#60;td valign="top" align="right" bgcolor="#E4E4E4"&#62;
            &#60;font size="-2"&#62;
            </xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text disable-output-escaping="yes">
            &#60;td valign="top" align="right" bgcolor="#F6F6F6"&#62;
            &#60;font size="-2"&#62;
            </xsl:text>
            </xsl:otherwise>
            </xsl:choose>
            <xsl:value-of select="@chairperson"/>
            <xsl:text disable-output-escaping="yes">
            &#60;/font&#62;
            &#60;/td&#62;
            </xsl:text>
        </xsl:when>
        <xsl:otherwise>
            <xsl:choose>
            <xsl:when test="count(preceding-sibling::session) mod 2 = 1">
                <xsl:text disable-output-escaping="yes">
                &#60;td valign="top" align="right" bgcolor="#E4E4E4"&#62;
                </xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text disable-output-escaping="yes">
                &#60;td valign="top" align="right" bgcolor="#F6F6F6"&#62;
                </xsl:text>
            </xsl:otherwise>
            </xsl:choose>
            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
            <xsl:text disable-output-escaping="yes">
            &#60;/td&#62;
            </xsl:text>
        </xsl:otherwise>
        </xsl:choose>
    </tr>
    </xsl:for-each>

    </table>
    </td></tr>        </xsl:if></table>
    </td>
</tr>
</table>
</xsl:template>

<xsl:template name="minutes">
      <xsl:if test="./minutesText != ''">
      <tr>
        <td align="center" style="padding-top:10px;padding-bottom:10px" colspan="2">
          <table border="1" bgcolor="white" cellpadding="2" align="center" width="100%">
            <tr>
              <td align="center"><b>Minutes</b></td>
            </tr>
            <tr>
                <td><xsl:apply-templates select="./minutesText"/></td>
            </tr>
          </table>
        </td>
      </tr>
      </xsl:if>
 </xsl:template>
</xsl:stylesheet>
