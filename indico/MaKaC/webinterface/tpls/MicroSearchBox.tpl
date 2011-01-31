<script type="text/javascript">

var state = false;
var dialog;

function switchBox(item)
{
	if (state)
	{
		closeSearchBox(item);
		state = false;
	}
	else
	{
		openSearchBox(item);
		state = true;
	}
}

function openSearchBox(item)
{
	item.style.background = '#AACCFF';
	$(item).oldsrc = item.src
	item.src = <%= closeIcon %>;

	dialog = new SimplePanel('microSearchBox',250, -1,document.body,'absolute');
	dialog.setStyle('UIMicroSearchBox');
	dialog.hide();
	dialog.setInnerHTML("<%= innerBox %>");

	var res = findPos(item);

	var offLeft = res[0]
	var offTop = res[1]

	// Prevent occlusion
	if (offLeft < 250)
	{
		dialog.placeAt(offLeft,offTop+item.clientHeight);
	}
	else
	{
		dialog.placeAt(offLeft-250+item.clientWidth,offTop+item.clientHeight);
	}

	Effect.Appear(dialog.mainPanel);
}

function closeSearchBox(item)
{
	item.src = item.oldsrc;
	item.style.background = 'none';

	Effect.Fade(dialog.mainPanel);
}

</script>