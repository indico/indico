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

<xsl:template match="repno">
	<xsl:value-of select="./rn" disable-output-escaping="yes"/>
</xsl:template>

<xsl:variable name="closed" select="/iconf/closed"/>

<xsl:template name="displayModifIcons">
    <xsl:param name="item"/>
    <xsl:param name="confId"/>
    <xsl:param name="sessId"/>
    <xsl:param name="sessCode"/>
    <xsl:param name="contId"/>
    <xsl:param name="subContId"/>
    <xsl:param name="uploadURL"/>
    <xsl:param name="manageLink"/>
    <xsl:param name="manageLinkBgColor">#ECECEC</xsl:param>
    <!--
        If true the menu is aligned to the right with respect
        to the popup menu arrow.
    -->
    <xsl:param name="alignMenuRight">false</xsl:param>
    <xsl:variable name="menuName">menu<xsl:value-of select="$confId"/><xsl:value-of select="translate($sessCode, '-','')"/><xsl:value-of select="$contId"/><xsl:value-of select="$subContId"/></xsl:variable>
    <xsl:if test="$closed = 'False' and ($item/modifyLink != '' or $item/materialLink != '' or $item/minutesLink != '')">
        <!-- script that creates a variable for a menu  -->

        <xsl:choose>
            <xsl:when test="$manageLink != ''">
                <xsl:text disable-output-escaping="yes"><![CDATA[<div class="manageLink" style="background: ]]></xsl:text>
                    <xsl:value-of select="$manageLinkBgColor"/>
                <xsl:text disable-output-escaping="yes"><![CDATA[;">]]></xsl:text>
                <xsl:text disable-output-escaping="yes"><![CDATA[<div class="dropDownMenu fakeLink" id="]]></xsl:text>
                    <xsl:value-of select="$menuName"/>
                <xsl:text disable-output-escaping="yes"><![CDATA[">Manage</div></div>]]></xsl:text>
            </xsl:when>
             <xsl:otherwise>
                <xsl:text disable-output-escaping="yes"><![CDATA[<span class="confModifIcon" id="]]></xsl:text>
                    <xsl:value-of select="$menuName"/>
                <xsl:text disable-output-escaping="yes"><![CDATA["></span>]]></xsl:text>
             </xsl:otherwise>
        </xsl:choose>

        <xsl:text disable-output-escaping="yes">
            <![CDATA[<script type="text/javascript"> $E(']]></xsl:text><xsl:value-of select="$menuName"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[').observeClick(function() {
            var element = $E(']]></xsl:text>
            <xsl:value-of select="$menuName"/><xsl:text disable-output-escaping="yes"><![CDATA[');
        ]]></xsl:text>
        <xsl:value-of select="$menuName"/><xsl:text disable-output-escaping="yes"><![CDATA[.open(element.getAbsolutePosition().x]]>
        </xsl:text>

        <xsl:if test="$alignMenuRight = 'true'">
            <xsl:text disable-output-escaping="yes"><![CDATA[+element.dom.offsetWidth+1]]></xsl:text>
        </xsl:if>

        <xsl:if test="$manageLink != ''">
            <xsl:text disable-output-escaping="yes"><![CDATA[+9]]></xsl:text>
        </xsl:if>

        <xsl:text disable-output-escaping="yes"><![CDATA[, element.getAbsolutePosition().y+element.dom.offsetHeight);});

            var ]]>
        </xsl:text>
        <xsl:value-of select="$menuName"/>
        <xsl:text disable-output-escaping="yes">
        <![CDATA[
            = new PopupMenu({
        ]]>
        </xsl:text>
        <xsl:choose>
            <xsl:when test="$item/modifyLink != '' and $sessCode = '' and $contId = '' and $subContId = ''">
            'Edit event': '<xsl:value-of select="$item/modifyLink"/>',
            </xsl:when>
            <xsl:when test="$item/modifyLink != '' and $subContId != 'null'">
            'Edit subcontribution': '<xsl:value-of select="$item/modifyLink"/>',
            </xsl:when>
            <xsl:when test="$item/modifyLink != '' and $contId != 'null'">
            'Edit contribution': '<xsl:value-of select="$item/modifyLink"/>',
            </xsl:when>
            <xsl:when test="$item/modifyLink != '' and $sessCode != 'null'">
            'Edit session': '<xsl:value-of select="$item/modifyLink"/>',
            </xsl:when>
            <xsl:when test="$item/modifyLink != ''">
            'Edit entry': '<xsl:value-of select="$item/modifyLink"/>',
            </xsl:when>
        </xsl:choose>
        <xsl:if test="$item/cloneLink != ''">
            'Clone event': '<xsl:value-of select="$item/cloneLink"/>',
        </xsl:if>
        <xsl:if test="$item/minutesLink != ''">
            'Edit minutes': function(m){IndicoUI.Dialogs.writeMinutes('<xsl:value-of select="$confId"/>',
            '<xsl:value-of select="$sessId"/>',
            '<xsl:value-of select="$contId"/>',
            '<xsl:value-of select="$subContId"/>');m.close();return false;},
        </xsl:if>
        <xsl:if test="$sessCode = '' and $contId = '' and $subContId = ''">
            'Compile minutes': function(m){if (confirm('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.')) {
            IndicoUI.Dialogs.writeMinutes('<xsl:value-of select="$confId"/>',
            '<xsl:value-of select="$sessId"/>',
            '<xsl:value-of select="$contId"/>',
            '<xsl:value-of select="$subContId"/>',true);m.close();}return false;},
        </xsl:if>
        <xsl:if test="$item/materialLink != ''">
            'Manage material': function(m){
                IndicoUI.Dialogs.Material.editor('<xsl:value-of select="$confId"/>',
                '<xsl:value-of select="$sessId"/>',
                '<xsl:value-of select="$contId"/>',
                '<xsl:value-of select="$subContId"/>',
                <xsl:value-of select="$item/parentProtection"/>,
                <xsl:value-of select="$item/materialList"/>,
                <xsl:value-of select="$uploadURL"/>,
                true);

                m.close();
                return false;
           }
        </xsl:if>
        <xsl:text disable-output-escaping="yes">
        <![CDATA[
        },[$E("]]></xsl:text>
        <xsl:value-of select="$menuName"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[")],null, false, ]]></xsl:text>
        <xsl:value-of select="$alignMenuRight"/>
        <xsl:text disable-output-escaping="yes"><![CDATA[);</script>]]></xsl:text>
    </xsl:if>

</xsl:template>



<xsl:template match="user">
	<xsl:param name="span" default=""/>
	<span class="{$span}">
	<xsl:apply-templates select="./name"/>
	<xsl:if test="./organization != ''">
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>(<xsl:value-of select="./organization" disable-output-escaping="yes"/>)
	</xsl:if>
	</span>
</xsl:template>

<xsl:template name="fulluser">
	<xsl:param name="span" default=""/>
	<span class="{$span}">
	<xsl:apply-templates select="./title"/>
	<xsl:apply-templates select="./name"/>
	<xsl:if test="./organization != ''">
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>(<xsl:value-of select="./organization" disable-output-escaping="yes"/>)
	</xsl:if>
	</span>
</xsl:template>

<xsl:template match="title">
	<xsl:if test=".!=''">
	<xsl:value-of select="."/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	</xsl:if>
</xsl:template>

<xsl:template match="VRVS">
  VRVS <xsl:value-of select="./description"/>
</xsl:template>

<xsl:template match="HERMES">
  HERMES <xsl:value-of select="./description"/>
</xsl:template>

<xsl:template match="EDIAL">
  eDial <xsl:value-of select="./description"/>
</xsl:template>

<xsl:template match="name">
	<xsl:value-of select="./@first" disable-output-escaping="yes"/>
	<xsl:if test="./@first!='' and ./@last!=''">
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	</xsl:if>
	<xsl:value-of select="./@last" disable-output-escaping="yes"/>
</xsl:template>



<xsl:template match="location">
    <xsl:param name="span"/>
    <xsl:if test="count(../../location/name)=0 or ../../location/name != ./name">
        <xsl:value-of select="./name"/>
	    <xsl:if test="./name != '' and ./room != '0--' and ./room != 'Select:' and ./room != ''">
        (
        </xsl:if>
    </xsl:if>
	<xsl:if test="./room != '0--' and ./room != 'Select:' and ./room != ''">
            <xsl:if test="./roomMapURL != ''">
            <xsl:text disable-output-escaping="yes">
			&#60;a href="
			</xsl:text>
            <xsl:value-of select="./roomMapURL" disable-output-escaping="yes"/>
            <xsl:text disable-output-escaping="yes">
			"&#62;
			</xsl:text>
			</xsl:if>
			<span class="{$span}">
			<xsl:value-of select="./room" disable-output-escaping="yes"/>
			</span>
			<xsl:text disable-output-escaping="yes">
			&#60;/a&#62;
			</xsl:text>
        <xsl:if test="count(../../location/name)=0 or ../../location/name != ./name">
	    <xsl:if test="./name != '' and ./room != '0--' and ./room != 'Select:' and ./room != ''">
		)
            </xsl:if>
        </xsl:if>
	</xsl:if>
</xsl:template>

<xsl:template match="supportEmail">
        <a href="mailto:{.}">
        <xsl:value-of select="."/>
        </a>
</xsl:template>

<xsl:template match="materialLink">
    <xsl:param name="fileType"/>
    <xsl:param name="imgURL"/>
    <xsl:param name="imgAlt"/>

    <xsl:if test="count(./files/file[type='$fileType']) = 1">
        <a href="{./files/file[type='$fileType'][1]/url}" class="material"><img src="{$imgURL}" border="0" alt="{$imgAlt}"/></a>
    </xsl:if>

    <xsl:if test="count(./files/file[type='$fileType']) &gt; 1">
        <xsl:variable name="materialMenuName">materialMenu<xsl:value-of select="./type"/><xsl:value-of select="$fileType"/><xsl:value-of select="$sessionId"/><xsl:value-of select="$contribId"/><xsl:value-of select="$subContId"/></xsl:variable>
            <a class="material">
                <div class="dropDownMaterialMenu" id="{$materialMenuName}">
                    <img src="{$imgURL}" border="0" alt="{$imgAlt}"/>
<!--                    <img src="images/pdf_small.png" border="0" alt="pdf file"/>-->
                </div>
            </a>
            <script type="text/javascript">
                $E('<xsl:value-of select="$materialMenuName"/>').observeClick(function() {
                    var elem = $E('<xsl:value-of select="$materialMenuName"/>');
                    var parentElem = $E(elem.dom.parentNode);
                    <xsl:value-of select="$materialMenuName"/>.open(parentElem.getAbsolutePosition().x, parentElem.getAbsolutePosition().y + parentElem.dom.offsetHeight);
                    }
                 );

                var <xsl:value-of select="$materialMenuName"/> = new PopupMenu({
                    <xsl:for-each select="./files/file[type='$fileType']">
                    '<xsl:value-of select="./name"/>':'<xsl:value-of select="./url"/>'
                    <xsl:if test="position() != last()">
                    ,
                    </xsl:if>
                    </xsl:for-each>
                    }, [$E("<xsl:value-of select="$materialMenuName"/>")], 'materialMenuPopupList', false, false);
            </script>
    </xsl:if>
</xsl:template>

<xsl:template match="material">
	<xsl:param name="sessionId"/>
	<xsl:param name="contribId"/>
    <xsl:param name="subContId"/>

    <span class="materialGroup">
        <a href="{./displayURL}" class="material materialGroup">
            <xsl:value-of select="./type"/>
        	<xsl:value-of select="./title"/>
            <xsl:if test="./locked = 'yes'">
                <img src="images/protected.png" border="0" alt="locked" style="margin-left: 3px;"/>
            </xsl:if>
        </a>

        <xsl:for-each select="./types/type">

            <xsl:variable name="typeName" select="./name"/>

            <xsl:if test="count(./../../files/file[type=$typeName]) = 1">
                <a href="{./../../files/file[type=$typeName][1]/url}" class="material"><img src="{./imgURL}" border="0" alt="{./imgAlt}"/></a>
            </xsl:if>

            <xsl:if test="count(./../../files/file[type=$typeName]) &gt; 1">
                <xsl:variable name="materialMenuName">materialMenu<xsl:value-of select="./../../title"/><xsl:value-of select="./name"/><xsl:value-of select="$sessionId"/><xsl:value-of select="$contribId"/><xsl:value-of select="$subContId"/></xsl:variable>
                    <a class="material dropDownMaterialMenu" id="{$materialMenuName}">
                        <img class="resourceIcon" src="{./imgURL}" border="0" alt="{./imgAlt}"/>
                        <img class="arrow" src="images/menu_arrow_black.png" border='0' alt="down arrow"/>
                    </a>
                    <script type="text/javascript">
                        $E('<xsl:value-of select="$materialMenuName"/>').observeClick(function() {
                            var elem = $E('<xsl:value-of select="$materialMenuName"/>');
                            <xsl:value-of select="$materialMenuName"/>.open(elem.getAbsolutePosition().x, elem.getAbsolutePosition().y + elem.dom.offsetHeight);
                            }
                         );

                        var <xsl:value-of select="$materialMenuName"/> = new PopupMenu({
                            <xsl:for-each select="./../../files/file[type=$typeName]">
                            '<xsl:value-of select="./name"/>':'<xsl:value-of select="./url"/>'
                            <xsl:if test="position() != last()">
                            ,
                            </xsl:if>
                            </xsl:for-each>
                            }, [$E("<xsl:value-of select="$materialMenuName"/>")], 'materialMenuPopupList', false, false);
                    </script>
            </xsl:if>

        </xsl:for-each>
    </span>
</xsl:template>

<xsl:template match="description|abstract|minutesText">
    <xsl:choose>
    <xsl:when test="contains(.,'&lt;p&gt;') or contains(.,'&lt;P&gt;') or contains(.,'&lt;p ') or contains(.,'&lt;P ') or contains(.,'&lt;br&gt;') or contains(.,'&lt;BR&gt;') or contains(.,'&lt;LI&gt;') or contains(.,'&lt;li&gt;')">
        <xsl:value-of select="." disable-output-escaping="yes"/>
    </xsl:when>
    <xsl:otherwise>
      <pre><xsl:value-of select="." disable-output-escaping="yes"/></pre>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
