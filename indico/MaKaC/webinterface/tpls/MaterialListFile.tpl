<li>
    <a href=${ fileAccessURL }>${ fileName }</a>
    ${ fileInfo }
    <input type="image" name="${ delName }" src="${ deleteIconURL }" alt="delete the file" onclick="return confirm('${ _("Are you sure you want to delete this file?")}');" style="vertical-align:middle;" />
        ${ fileActions }
</li>
