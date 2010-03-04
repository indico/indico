<?xml version='1.0'?>
<!-- $Id: indico.xsl,v 1.33 2009/06/24 14:03:25 jose Exp $

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

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- This template seems to not being used -->
  <xsl:template name="header">
    <td width="60%">
      <xsl:call-template name="displayModifIcons">
        <xsl:with-param name="item" select="."/>
        <xsl:with-param name="confId" select="/iconf/ID"/>
        <xsl:with-param name="sessId" value=""/>
        <xsl:with-param name="contId" value=""/>
        <xsl:with-param name="subContId" value=""/>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
      </xsl:call-template>
      <span class="titles">
        <xsl:value-of select="./title" disable-output-escaping="yes"/>
      </span>
    </td>
    <td width="1%" class="settings">
      <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
    </td>
    <td width="29%" class="settings">
      <xsl:choose>
        <xsl:when test="substring(./startDate,0,11) = substring(./endDate,0,11)">
          <b>
            <xsl:call-template name="prettydate">
              <!-- Fermi timezone awareness -->
              <xsl:with-param name="dat" select="substring(./startDate,0,21)"/>
            </xsl:call-template>
          </b>
          <br/> from <b>
            <xsl:value-of select="substring(./startDate,12,5)"/>
          </b> to <b>
            <xsl:value-of select="substring(./endDate,12,5)"/>
          </b>
          <xsl:value-of select="substring(./timezone,0,25)"/>
        </xsl:when>
        <xsl:otherwise> from <b>
            <xsl:call-template name="prettydate">
              <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
            </xsl:call-template> (<xsl:value-of select="substring(./startDate,12,5)"/>) </b><br/> to <b>
            <xsl:call-template name="prettydate">
              <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
            </xsl:call-template> (<xsl:value-of select="substring(./endDate,12,5)"/>) </b>
            (<xsl:value-of select="substring(./timezone,0,25)"/>) </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
        <br/>at <b>
          <xsl:apply-templates select="./location">
            <xsl:with-param name="span">author</xsl:with-param>
          </xsl:apply-templates>
        </b>
      </xsl:if>
      <xsl:if test="count(child::chair) != 0">
        <br/>chaired by: <b>
          <xsl:apply-templates select="./chair"/>
        </b>
      </xsl:if>
      <xsl:apply-templates select="./supportEmail"/>
      <xsl:for-each select="./repno">
        <br/>
        <xsl:apply-templates select="."/>
      </xsl:for-each>
    </td>
  </xsl:template>


  <xsl:template name="body">
    <xsl:param name="minutes">off</xsl:param>
    <ul class="dayList">
      <xsl:for-each select="./session|./contribution|./break">
        <xsl:variable name="ids" select="./ID"/>
        <xsl:variable name="day" select="substring(./startDate,0,11)"/>

        <xsl:if
          test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
          <xsl:text disable-output-escaping="yes">&lt;li&gt;</xsl:text>
          <div style="width: 100%;">
            <a name="{$day}"/>
            <span class="day">
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
              </xsl:call-template>
            </span>
          </div>
          <xsl:text disable-output-escaping="yes">&lt;ul class="meetingTimetable"&gt;</xsl:text>
        </xsl:if>
        <xsl:apply-templates select=".">
          <xsl:with-param name="minutes" select="$minutes"/>
        </xsl:apply-templates>
        <xsl:if
          test="count(following::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(following::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(following::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
          <xsl:text disable-output-escaping="yes">&lt;/ul&gt;</xsl:text>
          <xsl:text disable-output-escaping="yes">&lt;/li&gt;</xsl:text>
        </xsl:if>
      </xsl:for-each>
    </ul>
  </xsl:template>


  <xsl:template match="session">
    <xsl:param name="minutes">off</xsl:param>
    <xsl:param name="titleClass">topLevelTitle</xsl:param>

    <li class="meetingSession">
      <span class="containerTitle confModifPadding">
        <a name="{./ID}"/>
          <xsl:call-template name="displayModifIcons">
            <xsl:with-param name="item" select="."/>
            <xsl:with-param name="confId" select="../ID"/>
            <xsl:with-param name="sessId" select="./ID"/>
            <xsl:with-param name="contId">null</xsl:with-param>
            <xsl:with-param name="alignMenuRight">true</xsl:with-param>
            <xsl:with-param name="subContId">null</xsl:with-param>
            <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.session</xsl:with-param>
          </xsl:call-template>

        <span class="topLevelTime">
          <xsl:value-of select="substring(./startDate,12,5)"/> - <xsl:value-of
            select="substring(./endDate,12,5)"/>
        </span>

        <span class="{$titleClass}">
          <xsl:value-of select="./title" disable-output-escaping="yes"/>
        </span>
      </span>

      <xsl:if test="./description != ''">
        <span class="description"><xsl:apply-templates select="./description"/></span>
      </xsl:if>

      <table class="sessionDetails">
        <tbody>

          <xsl:if test="count(child::convener) != 0">
            <tr>
              <td class="leftCol">Convener:</td>
              <td>
                <xsl:apply-templates select="./convener"/>
              </td>
            </tr>
          </xsl:if>
          <xsl:if
            test="count(./location) != 0 and normalize-space(string(../location)) != normalize-space(string(./location))">
            <tr>
              <td class="leftCol">Location:</td>
              <td>
                <xsl:apply-templates select="./location">
                  <xsl:with-param name="span"/>
                </xsl:apply-templates>
              </td>
            </tr>
          </xsl:if>
          <xsl:if test="count(child::material) != 0">
            <tr>
              <td class="leftCol">Material:</td>
              <td>
                <xsl:for-each select="./material">
                  <xsl:apply-templates select=".">
                    <xsl:with-param name="sessionId" select="../ID"/>
                  </xsl:apply-templates>
                </xsl:for-each>
              </td>
            </tr>
          </xsl:if>

          <xsl:if test="./participants != ''">
            <br/> Participants: <xsl:value-of select="./participants" disable-output-escaping="yes"
            /><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
          </xsl:if>
        </tbody>
      </table>

      <xsl:if test="$minutes = 'on'">
        <xsl:for-each select="./material">
          <xsl:if test="./minutesText != ''">
            <div class="minutesTable">
              <h2>Minutes</h2>
              <span>
                <xsl:apply-templates select="./minutesText"/>
              </span>
            </div>
          </xsl:if>
        </xsl:for-each>
      </xsl:if>
      <xsl:if test="count(child::contribution)+count(child::break) != 0">
        <ul class="meetingSubTimetable">
          <xsl:for-each select="./contribution|./break">
            <xsl:apply-templates select=".">
              <xsl:with-param name="minutes" select="$minutes"/>
              <xsl:with-param name="hideEndTime">true</xsl:with-param>
              <xsl:with-param name="timeClass">subEventLevelTime</xsl:with-param>
              <xsl:with-param name="titleClass">subEventLevelTitle</xsl:with-param>
              <xsl:with-param name="abstractClass">subEventLevelAbstract</xsl:with-param>
              <xsl:with-param name="scListClass">subEventLevelSCList</xsl:with-param>
            </xsl:apply-templates>
          </xsl:for-each>
        </ul>
      </xsl:if>
    </li>
  </xsl:template>



  <xsl:template match="contribution">
    <xsl:param name="minutes">off</xsl:param>
    <xsl:param name="hideEndTime">false</xsl:param>
    <xsl:param name="timeClass">topLevelTime</xsl:param>
    <xsl:param name="titleClass">topLevelTitle</xsl:param>
    <xsl:param name="abstractClass">topLevelAbstract</xsl:param>
    <xsl:param name="scListClass">topLevelSCList</xsl:param>


    <xsl:variable name="idt" select="./ID"/>

    <li class="meetingContrib">

      <xsl:if test="name(..) = 'session'">
        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../../ID"/>
          <xsl:with-param name="sessId" select="../ID"/>
          <xsl:with-param name="contId" select="./ID"/>
          <xsl:with-param name="alignMenuRight">true</xsl:with-param>
          <xsl:with-param name="subContId">null</xsl:with-param>
          <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>
      </xsl:if>
      <xsl:if test="name(..) != 'session'">
          <xsl:call-template name="displayModifIcons">
            <xsl:with-param name="item" select="."/>
            <xsl:with-param name="confId" select="../ID"/>
            <xsl:with-param name="sessId">null</xsl:with-param>
            <xsl:with-param name="contId" select="./ID"/>
            <xsl:with-param name="alignMenuRight">true</xsl:with-param>
            <xsl:with-param name="subContId">null</xsl:with-param>
            <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
          </xsl:call-template>
      </xsl:if>

      <span class="{$timeClass}">
          <xsl:value-of select="substring(./startDate,12,5)"/>
          <xsl:if test="$hideEndTime = 'false'">
             - <xsl:value-of select="substring(./endDate,12,5)"/>
          </xsl:if>
      </span>

      <span class="confModifPadding">
          <span class="{$titleClass}">
            <xsl:value-of select="./title" disable-output-escaping="yes"/>
          </span>

          <xsl:if test="./duration != '00:00'">
            <em><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
              <xsl:call-template name="prettyduration">
                <xsl:with-param name="duration" select="./duration"/>
              </xsl:call-template>
            </em>
          </xsl:if>

          <xsl:if
            test="count(./location) != 0 and normalize-space(string(../location)) != normalize-space(string(./location))"
            >
            <span style="margin-left: 15px;">(
            <xsl:apply-templates select="./location">
              <xsl:with-param name="span"/>
            </xsl:apply-templates>)</span>
          </xsl:if>


      </span>

      <xsl:if test="string-length(./abstract) > 1">
        <br /><span class="description"><xsl:apply-templates select="./abstract"/></span>
      </xsl:if>

      <table class="sessionDetails">
        <tbody>

          <!-- <xsl:if test="./category != '' and ./category != ' '">
            <span class="headerselected">
              <xsl:value-of select="./category"/>
            </span>
            <br/>
          </xsl:if>-->

          <xsl:if test="count(child::speakers) != 0">
            <tr>
              <td class="leftCol">Speakers:</td>
              <td><xsl:apply-templates select="./speakers"/></td>
            </tr>
          </xsl:if>

          <xsl:if test="./broadcasturl != ''">
            <tr>
              <td class="leftCol">Video broadcast</td>
              <td><a href="{./broadcasturl}">View now</a></td>
            </tr>
          </xsl:if>

          <xsl:if test="count(child::repno) != 0">
            ( <xsl:for-each select="./repno">
              <xsl:apply-templates select="."/>
              <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
            </xsl:for-each> )
          </xsl:if>

          <xsl:if test="count(child::material) != 0">
            <tr>
              <td class="leftCol">Material:</td><td>
                <xsl:for-each select="./material">
                  <xsl:apply-templates select=".">
                    <xsl:with-param name="contribId" select="../ID"/>
                  </xsl:apply-templates>
                </xsl:for-each>
              </td>
            </tr>
          </xsl:if>

        </tbody>
      </table>

      <xsl:if test="count(subcontribution) != 0">
          <ul class="{$scListClass}">
            <xsl:for-each select="subcontribution">
              <xsl:apply-templates select=".">
                <xsl:with-param name="minutes" select="$minutes"/>
              </xsl:apply-templates>
            </xsl:for-each>
          </ul>
      </xsl:if>

          <xsl:if test="$minutes = 'on'">
            <xsl:for-each select="./material">
              <xsl:if test="./minutesText != ''">
                <div class="minutesTable">
                    <h2>Minutes</h2>
                    <span><xsl:apply-templates select="./minutesText"/></span>
                </div>
              </xsl:if>
            </xsl:for-each>
          </xsl:if>
    </li>
  </xsl:template>



  <xsl:template match="subcontribution">
    <xsl:param name="minutes">off</xsl:param>
    <xsl:variable name="idt" select="./ID"/>
    <li>
      <xsl:if test="name(../..) = 'session'">
          <xsl:call-template name="displayModifIcons">
            <xsl:with-param name="item" select="."/>
            <xsl:with-param name="confId" select="../../../ID"/>
            <xsl:with-param name="sessId" select="../../ID"/>
            <xsl:with-param name="contId" select="../ID"/>
            <xsl:with-param name="alignMenuRight">true</xsl:with-param>
            <xsl:with-param name="subContId" select="./ID"/>
            <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
          </xsl:call-template>
      </xsl:if>
      <xsl:if test="name(../..) != 'session'">
          <xsl:call-template name="displayModifIcons">
            <xsl:with-param name="item" select="."/>
            <xsl:with-param name="confId" select="../../ID"/>
            <xsl:with-param name="sessId">null</xsl:with-param>
            <xsl:with-param name="alignMenuRight">true</xsl:with-param>
            <xsl:with-param name="contId" select="../ID"/>
            <xsl:with-param name="subContId" select="./ID"/>
            <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
          </xsl:call-template>
      </xsl:if>

      <span class="subLevelTitle confModifPadding">
        <xsl:value-of select="./title" disable-output-escaping="yes"/>
      </span>

      <xsl:if test="./duration != '00:00'">
        <em><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
          <xsl:call-template name="prettyduration">
            <xsl:with-param name="duration" select="./duration"/>
          </xsl:call-template>
        </em>
      </xsl:if>

      <xsl:if test="./abstract != ''">
        <span class="description"><xsl:apply-templates select="./abstract"/></span>
      </xsl:if>

      <table class="sessionDetails">
        <tbody>

      <xsl:if test="count(child::repno) != 0">( <xsl:for-each select="./repno">
          <xsl:apply-templates select="."/>
          <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
        </xsl:for-each> )</xsl:if>

        <xsl:if test="count(child::speakers) != 0">
          <tr>
            <td class="leftCol">Speakers:</td>
            <td><xsl:apply-templates select="./speakers"/></td>
          </tr>
        </xsl:if>

        <xsl:if test="count(child::material) != 0">
        <tr>
          <td class="leftCol">Material:</td>
          <td>
        <xsl:for-each select="./material">
          <xsl:apply-templates select=".">
            <xsl:with-param name="contribId" select="../../ID"/>
            <xsl:with-param name="subContId" select="../ID"/>
          </xsl:apply-templates>
        </xsl:for-each>
            </td></tr>
      </xsl:if>

        </tbody>
      </table>
            <xsl:if test="$minutes = 'on'">
            <xsl:for-each select="./material">
              <xsl:if test="./minutesText != ''">
                <div class="minutesTable">
                    <h2>Minutes</h2>
                    <span><xsl:apply-templates select="./minutesText"/></span>
                </div>
              </xsl:if>
            </xsl:for-each>
          </xsl:if>

    </li>
  </xsl:template>




  <xsl:template match="break">
    <xsl:param name="hideEndTime">false</xsl:param>
    <xsl:param name="timeClass">topLevelTime</xsl:param>
    <xsl:param name="titleClass">topLevelTitle</xsl:param>

    <li class="breakListItem">
      <span class="{$timeClass}">
        <xsl:value-of select="substring(./startDate,12,5)"/>
        <xsl:if test="$hideEndTime = 'false'">
          - <xsl:value-of select="substring(./endDate,12,5)"/>
        </xsl:if>
      </span>

      <span class="confModifPadding">
        <span class="{$titleClass}" style="color: #69856e">
          <xsl:value-of select="./name" disable-output-escaping="yes"/>
        </span>
        <xsl:if test="$hideEndTime = 'true'">
          <xsl:if test="./duration != '00:00'">
            <em><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
              <xsl:call-template name="prettyduration">
                <xsl:with-param name="duration" select="./duration"/>
              </xsl:call-template>
            </em>
          </xsl:if>
        </xsl:if>
      </span>

      <xsl:if test="./broadcasturl != ''">
        <br/>
        <a href="{./broadcasturl}">
          <br/>(video broadcast)</a>
      </xsl:if>
     <xsl:if test="count(./location) != 0 and normalize-space(string(../location)) != normalize-space(string(./location))"
        > (<xsl:apply-templates select="./location"/>) </xsl:if>
      <xsl:if test="./description != ''">
        <span class="description">
        <xsl:apply-templates select="./description"/>
        </span>
      </xsl:if>
    </li>
  </xsl:template>




  <xsl:template match="chair|announcer">
    <xsl:for-each select="./UnformatedUser|./user">
      <xsl:apply-templates select=".">
        <xsl:with-param name="span">author</xsl:with-param>
      </xsl:apply-templates>
      <xsl:if test="count(following-sibling::user) != 0">, </xsl:if>
    </xsl:for-each>
  </xsl:template>




  <xsl:template match="convener|speakers">
    <xsl:for-each select="./user|./UnformatedUser">
      <xsl:apply-templates select=".">
        <xsl:with-param name="span"/>
      </xsl:apply-templates>
      <xsl:if test="count(following-sibling::user) != 0"
        >,<xsl:text disable-output-escaping="yes"> </xsl:text></xsl:if>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="header2">
    <xsl:param name="minutes">off</xsl:param>

    <table class="eventDetails">
      <tbody>

        <xsl:if test="./description != ''">
          <tr>
            <td class="leftCol">Description</td>
            <td style="font-style: italic;">
              <xsl:apply-templates select="./description"/>
            </td>
          </tr>
        </xsl:if>

        <xsl:if test="count(./videoconference) != 0">
          <tr>
            <td class="leftCol">Videoconference</td>
            <td valign="top">
              <xsl:for-each select="./videoconference">
                <xsl:apply-templates select="."/>
              </xsl:for-each>
            </td>
          </tr>
        </xsl:if>

        <xsl:if test="count(./audioconference) != 0">
          <tr>
            <td class="leftCol">Audioconference</td>
            <td>
              <xsl:for-each select="./audioconference">
                <xsl:apply-templates select="."/>
              </xsl:for-each>
            </td>
          </tr>
        </xsl:if>

        <xsl:if test="./participants != ''">
          <tr>
            <td class="leftCol">Participants</td>
            <td>
              <xsl:value-of select="./participants" disable-output-escaping="yes"/>
            </td>
          </tr>
        </xsl:if>


          <!--
            Handle all related to materials

            This uses an ugly hack since the links to same lecture with different dates
            as well as links to webcasts are treared as materials. The material table row
            is hidden by default and is later displayed using javascript if a material is found
          -->

          <tr id="webCastRow" style="display: none">
            <xsl:for-each select="./material">
            <xsl:if test="./title = 'live webcast' or ./title = 'forthcoming webcast'">
            <td class="leftCol">
              <xsl:if test="./title='live webcast'">
              Live Webcast
              </xsl:if>
              <xsl:if test="./title='forthcoming webcast'">
              Webcast
              </xsl:if>
            </td>
            </xsl:if>
            </xsl:for-each>
            <td>
              <xsl:for-each select="./material">
                <xsl:if test="./title = 'live webcast' or ./title = 'forthcoming webcast'">
                  <!-- Show the table row containing info about the webcast -->
                  <xsl:text disable-output-escaping="yes">
                    <![CDATA[
                        <script type="text/javascript">
                          $E('webCastRow').dom.style.display = ''
                        </script>
                      ]]>
                  </xsl:text>
                </xsl:if>


                <xsl:if test="./title='live webcast'">
                  <a href="{./displayURL}">
                    <strong>View the live webcast</strong>
                  </a>
                  <xsl:if test="./locked = 'yes'">
                    <img src="images/protected.png" border="0" alt="locked" style="margin-left: 3px;"/>
                  </xsl:if>
                </xsl:if>

                <xsl:if test="./title='forthcoming webcast'">
                  Please note that this event will be available <em>live</em> via the
                  <a href="{./displayURL}">
                    <strong>Webcast Service</strong>.
                  </a>
                </xsl:if>

              </xsl:for-each>
            </td>
          </tr>


          <tr id="materialList" style="display: none">
            <td class="leftCol">Material</td>
            <td>
              <div class="materialList clearfix">
                <xsl:for-each select="./material">
                  <xsl:if test="./title!='live webcast' and ./title!='forthcoming webcast' and ./title!='part1' and ./title!='part2' and ./title!='part3' and ./title!='part4' and ./title!='part5' and ./title!='part6' and ./title!='part7' and ./title!='part8' and ./title!='part9' and ./title!='part10'">
                    <!-- Show the material table row -->
                    <xsl:text disable-output-escaping="yes">
                      <![CDATA[
                        <script type="text/javascript">
                          $E('materialList').dom.style.display = ''
                        </script>
                      ]]>
                    </xsl:text>

                    <xsl:apply-templates select="."/>

                  </xsl:if>
                </xsl:for-each>
                </div>

              <xsl:if test="$minutes = 'on'">
                <xsl:for-each select="./material">
                  <xsl:if test="./minutesText != ''">
                    <center>
                      <div class="minutesTable">
                        <h2>Minutes</h2>
                        <span>
                          <xsl:apply-templates select="./minutesText"/>
                        </span>
                      </div>
                    </center>
                  </xsl:if>
                </xsl:for-each>
              </xsl:if>
            </td>
          </tr>

          <tr id="lectureLinks" style="display: none">
            <td class="leftCol">Other occasions</td>
            <td>
              <xsl:for-each select="./material">
                <xsl:sort select="./title"/>
                <xsl:if
                  test="./title='part1' or ./title='part2' or ./title='part3' or ./title='part4' or ./title='part5' or ./title='part6' or ./title='part7' or ./title='part8' or ./title='part9' or ./title='part10'">

                  <!-- Show the table row containing links to other instances of this lecture -->
                  <xsl:text disable-output-escaping="yes">
                    <![CDATA[
                        <script type="text/javascript">
                          $E('lectureLinks').dom.style.display = ''
                        </script>
                      ]]>
                  </xsl:text>

                  <a href="materialDisplay.py?materialId={./ID}&#38;confId={/iconf/ID}">
                    <img src="images/{./title}.png" alt="{./title}"/>
                  </a>
                  <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                </xsl:if>
              </xsl:for-each>
            </td>
          </tr>

        <!--
            End of materials
        -->

        <xsl:if test="./apply != ''">
          <tr>
            <td class="leftCol">Registration</td>
            <td>
              Want to participate?
              <span class="fakeLink" id="applyLink">Apply here</span>
              <xsl:text disable-output-escaping="yes"><![CDATA[
              <script type="text/javascript">
                $E('applyLink').observeClick(function() {new ApplyForParticipationPopup("]]></xsl:text>
                    <xsl:value-of select="./ID" disable-output-escaping="yes"/>
                <xsl:text disable-output-escaping="yes"><![CDATA[")});
              </script>
              ]]></xsl:text>
            </td>
          </tr>
        </xsl:if>

        <xsl:if test="./evaluationLink != ''">
          <tr>
            <td class="leftCol">Evaluation</td>
            <td>
              <a href="{./evaluationLink}">Evaluate this event</a>
            </td>
          </tr>
        </xsl:if>


        <xsl:if test="./organiser != ''">
          <tr>
            <td class="leftCol">Organised by</td>
            <td>
              <xsl:value-of select="./organiser" disable-output-escaping="yes"/>
            </td>
          </tr>
        </xsl:if>

        <xsl:if test="count(./plugins/collaboration/booking) != 0">
          <xsl:variable name="collaborationToday" select="./plugins/collaboration/todayReference"/>
          <xsl:variable name="collaborationTomorrow" select="./plugins/collaboration/tomorrowReference"/>
          <tr>
            <td class="leftCol">Video Services</td>
            <td>
              <div>
              <xsl:for-each select="./plugins/collaboration/booking">

                <xsl:if test="position() = 3">
                  <div id="collShowBookingsDiv">
                    <span class="collShowHideBookingsText">
                      <xsl:text>There are </xsl:text>
                      <xsl:if test="./kind = 'ongoing'">
                        <xsl:value-of select="1 + count(following-sibling::booking[kind = 'ongoing'])"/>
                        <xsl:text> more ongoing bookings </xsl:text>
                        <xsl:if test="count(following-sibling::booking[kind = 'scheduled']) &gt; 0">
                          <xsl:text> and </xsl:text>
                          <xsl:value-of select="count(following-sibling::booking[kind = 'scheduled'])"/>
                          <xsl:text> more scheduled bookings.</xsl:text>
                        </xsl:if>
                      </xsl:if>
                      <xsl:if test="./kind = 'scheduled'">
                        <xsl:value-of select="1 + count(following-sibling::booking[kind = 'scheduled'])"/>
                        <xsl:text> more scheduled bookings.</xsl:text>
                      </xsl:if>

                    </span>
                    <span id="collShowBookings" class="fakeLink collShowBookingsText">
                      Show
                    </span>
                  </div>
                  <xsl:text disable-output-escaping="yes"><![CDATA[
              </div>
              <div id="collHiddenBookings" style="visibility: hidden; overflow: hidden;">
                  ]]></xsl:text>
                </xsl:if>

                <!-- Start of a booking line -->
                <div class="collaborationDisplayBookingLine">
                  <xsl:if test="count(child::information) = 0">
                    <span class="collaborationDisplayBookingTitle"><xsl:value-of select="./title"/></span>
                    <xsl:text>:</xsl:text>
                  </xsl:if>

                  <xsl:if test="count(child::information) = 1">
                    <span class="fakeLink" id="collaborationBookingTitle{./id}"><xsl:value-of select="./title"/></span>
                    <xsl:text>:</xsl:text>

                    <xsl:text disable-output-escaping="yes"><![CDATA[
                    <script type="text/javascript">

                      $E('collaborationBookingTitle]]></xsl:text>
                        <xsl:value-of select="./id" disable-output-escaping="yes"/>
                        <xsl:text disable-output-escaping="yes"><![CDATA[').dom.onmouseover = function (event) {
                          IndicoUI.Widgets.Generic.tooltip($E('collaborationBookingTitle]]></xsl:text>
                            <xsl:value-of select="./id" disable-output-escaping="yes"/>
                            <xsl:text disable-output-escaping="yes"><![CDATA[').dom, event, ]]></xsl:text>
                              <xsl:text disable-output-escaping="yes">'&lt;div class=&quot;collaborationLinkTooltipMeetingLecture&quot;&gt;</xsl:text>
                              <xsl:text>Click here to show / hide detailed information.</xsl:text>
                              <xsl:text disable-output-escaping="yes">&lt;/div&gt;'</xsl:text>
                              <xsl:text disable-output-escaping="yes"><![CDATA[
                              );
                        }

                      var bookingInfoState]]></xsl:text>
                        <xsl:value-of select="./id" disable-output-escaping="yes"/>
                      <xsl:text disable-output-escaping="yes"><![CDATA[ = false;
                      $E('collaborationBookingTitle]]></xsl:text>
                        <xsl:value-of select="./id" disable-output-escaping="yes"/>
                      <xsl:text disable-output-escaping="yes"><![CDATA[').observeClick(function() {
                        if (bookingInfoState]]></xsl:text>
                        <xsl:value-of select="./id" disable-output-escaping="yes"/>
                      <xsl:text disable-output-escaping="yes"><![CDATA[) {
                        IndicoUI.Effect.disappear($E('collaborationInfoLine]]></xsl:text>
                        <xsl:value-of select="./id" disable-output-escaping="yes"/>
                        <xsl:text disable-output-escaping="yes"><![CDATA['));
                      } else {
                        IndicoUI.Effect.appear($E('collaborationInfoLine]]></xsl:text>
                        <xsl:value-of select="./id" disable-output-escaping="yes"/>
                        <xsl:text disable-output-escaping="yes"><![CDATA['));
                      }
                      bookingInfoState]]></xsl:text>
                      <xsl:value-of select="./id" disable-output-escaping="yes"/>
                    <xsl:text disable-output-escaping="yes"><![CDATA[ = !bookingInfoState]]></xsl:text>
                      <xsl:value-of select="./id" disable-output-escaping="yes"/>
                    <xsl:text disable-output-escaping="yes"><![CDATA[
                    });
                  </script>
                    ]]></xsl:text>
                  </xsl:if>

                  <xsl:choose>
                    <xsl:when test="./kind = 'scheduled' and substring(./startDate,0,11) = substring(./endDate,0,11)">
                      <!-- Starting and ending day is same, no need to print day twice -->
                      <xsl:choose>
                        <xsl:when test="$collaborationToday = substring(./startDate,0,11)">
                          <xsl:text> today </xsl:text>
                        </xsl:when>
                        <xsl:when test="$collaborationTomorrow = substring(./startDate,0,11)">
                          <xsl:text> tomorrow </xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                          <xsl:call-template name="shortDate">
                            <xsl:with-param name="dat" select="substring(./startDate,0,21)"/>
                          </xsl:call-template>
                        </xsl:otherwise>
                      </xsl:choose>
                      <xsl:text> from </xsl:text>
                      <xsl:value-of select="substring(./startDate,12,5)"/>
                      <xsl:text> to </xsl:text>
                      <xsl:value-of select="substring(./endDate,12,5)"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <!-- Starting and ending day are different -->
                      <xsl:if test="./kind = 'scheduled'">
                        <xsl:text> from </xsl:text>
                        <xsl:choose>
                          <xsl:when test="$collaborationToday = substring(./startDate,0,11)">
                            <xsl:text> today at </xsl:text>
                          </xsl:when>
                          <xsl:when test="$collaborationTomorrow = substring(./startDate,0,11)">
                            <xsl:text> tomorrow at </xsl:text>
                          </xsl:when>
                          <xsl:otherwise>
                            <xsl:call-template name="shortDate">
                              <xsl:with-param name="dat" select="substring(./startDate,0,21)"/>
                            </xsl:call-template>
                            <xsl:text> at </xsl:text>
                          </xsl:otherwise>
                        </xsl:choose>
                        <xsl:value-of select="substring(./startDate,12,5)"/>
                        <xsl:text> until </xsl:text>
                      </xsl:if>
                      <xsl:if test="./kind = 'ongoing'">
                        <xsl:text> ongoing until </xsl:text>
                      </xsl:if>


                      <xsl:choose>
                        <xsl:when test="$collaborationToday = substring(./endDate,0,11)">
                          <xsl:text> today at </xsl:text>
                        </xsl:when>
                        <xsl:when test="$collaborationTomorrow = substring(./endDate,0,11)">
                          <xsl:text> tomorrow at </xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                          <xsl:call-template name="shortDate">
                            <xsl:with-param name="dat" select="substring(./endDate,0,21)"/>
                          </xsl:call-template>
                          <xsl:text> at </xsl:text>
                        </xsl:otherwise>
                      </xsl:choose>
                      <xsl:value-of select="substring(./endDate,12,5)"/>
                    </xsl:otherwise>
                  </xsl:choose>

                  <xsl:text> (</xsl:text>
                  <xsl:value-of select="./typeDisplayName"/>
                  <xsl:text>) </xsl:text>

                  <xsl:if test="count(child::launchInfo) = 1">
                    <a href="{./launchInfo/launchLink}" id="bookingLaunchLink{./id}">
                      <xsl:value-of select="./launchInfo/launchText"/>
                    </a>
                    <xsl:text disable-output-escaping="yes"><![CDATA[
                      <script type="text/javascript">
                        $E('bookingLaunchLink]]></xsl:text>
                          <xsl:value-of select="./id" disable-output-escaping="yes"/>
                          <xsl:text disable-output-escaping="yes"><![CDATA[').dom.onmouseover = function (event) {
                            IndicoUI.Widgets.Generic.tooltip($E('bookingLaunchLink]]></xsl:text>
                              <xsl:value-of select="./id" disable-output-escaping="yes"/>
                              <xsl:text disable-output-escaping="yes"><![CDATA[').dom, event, ]]></xsl:text>
                                <xsl:text disable-output-escaping="yes">'&lt;div class=&quot;collaborationLinkTooltipMeetingLecture&quot;&gt;</xsl:text>
                                <xsl:value-of select="./launchInfo/launchTooltip" disable-output-escaping="yes"/>
                                <xsl:text disable-output-escaping="yes">&lt;/div&gt;'</xsl:text>
                                <xsl:text disable-output-escaping="yes"><![CDATA[
                                );
                          }
                      </script>
                    ]]></xsl:text>
                  </xsl:if>

                  <xsl:if test="count(child::information) = 1">
                  <!-- Start of a booking info line -->
                  <div class="collaborationDisplayInfoLine" id="collaborationInfoLine{./id}" style="display:none;">
                    <table>
                      <tbody>
                        <xsl:for-each select="./information/section">
                          <tr>
                            <td class="collaborationDisplayInfoLeftCol">
                              <span><xsl:value-of select="./title"/></span>
                            </td>
                            <td class="collaborationDisplayInfoRightCol">
                              <xsl:for-each select="./line">
                                <div>
                                  <xsl:value-of select="."/>
                                </div>
                              </xsl:for-each>
                            </td>
                          </tr>
                        </xsl:for-each>
                      </tbody>
                    </table>
                  </div>
                  </xsl:if>
                <!-- End of a booking info line -->
                </div>
                <!-- End of a booking line -->
              </xsl:for-each>
              <xsl:if test="count(./plugins/collaboration/booking) > 2">
                <div class="collHideBookingsDiv">
                  <span class="fakeLink collHideBookingsText" id="collHideBookings">Hide additional bookings</span>
                </div>
              </xsl:if>
              </div>
            </td>
          </tr>

        </xsl:if>


        <xsl:if test="./supportEmail != ''">
          <tr>
            <td class="leftCol">
                <xsl:value-of select="./supportEmail/@caption" />
            </td>
            <td>
              <xsl:apply-templates select="./supportEmail"/>
            </td>
          </tr>
        </xsl:if>

      </tbody>
    </table>

    <xsl:if test="count(./plugins/collaboration/booking) != 0">
        <xsl:text disable-output-escaping="yes"><![CDATA[
        <script type="text/javascript">
          var hideHook = function() {
              IndicoUI.Effect.appear($E('collShowBookingsDiv'));
          }

          if (exists($E('collHiddenBookings'))) {
            var height = IndicoUI.Effect.prepareForSlide('collHiddenBookings', true);
            $E('collShowBookings').observeClick(function() {
              IndicoUI.Effect.disappear($E('collShowBookingsDiv'));
              IndicoUI.Effect.slide('collHiddenBookings', height);
              IndicoUI.Effect.appear($E('collHideBookings'));
            });
            $E('collHideBookings').observeClick(function() {
              height = $E('collHiddenBookings').dom.offsetHeight;
              IndicoUI.Effect.slide('collHiddenBookings', height, null, hideHook);
            });
          }
        </script>
        ]]></xsl:text>
    </xsl:if>

  </xsl:template>

</xsl:stylesheet>