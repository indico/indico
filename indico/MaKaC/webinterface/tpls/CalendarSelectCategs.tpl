
<script LANGUAGE="JavaScript">

function alerta(id){

    b=document.links

    a=document.getElementById(id)

    if (a.checked){
     
        j=0
    
        while (j<b.length){
            
            
            lin=b[j]
             
            
            if (lin.href.indexOf("xs")!=-1){
                
                lin.href=lin.href+"&selCateg="+a.value
            }
            j=j+1
        }
        
    } else {
        
        caden="&selCateg="+a.value
        
        j=0
            
        while (j<b.length){
         
            if (b[j].href.indexOf("xs")!=-1){
              
                firstindex=b[j].href.indexOf(caden)
               
                aux=b[j].href.substring(0,firstindex)
                 
                lastindex=firstindex+caden.length
              
                aux2=b[j].href.substring(lastindex)
                                
                b[j].href=aux+aux2
                   
            }

            j++

        }

    }

}
</script>





<table align="center">
<tr>
  <td>
    <form name="formulary" action="%(calendarURL)s" method="GET">
    %(locatorNoCategs)s
     <%= _("Select the categories you want to appear in the calendar")%>
    <br>%(categs)s
    <br>
    <input type="submit" class="btn" value="<%= _("ok")%>">
    </form>
  </td>
</tr>
<tr>
  <td>
    <form action="%(calendarURL)s" method="GET">
    %(locator)s
    <input type="submit" class="btn" value="<%= _("cancel")%>">
    </form>
  </td>
</tr>
</table>