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
<xsl:include href="include/lectureBasics.xsl"/>
<xsl:output method="html"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">

   <div class="eventWrapper">
   
      
      <div class="lectureEventHeader">
         
         <xsl:call-template name="eventInfoBox"/>    
         
      </div>
      <div class="lectureEventBody">
         <xsl:call-template name="header2"/>
      </div>
      
   </div>

</xsl:template>


</xsl:stylesheet>
