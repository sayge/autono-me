{parent mainlayout.tpl}
<h2>Sharing information for #NAME#</h2>
<div style="position:relative; left:100px;">
<div style="font-face: Arial, Helvetica, sans-serif; font-size:12pt;">
Add a new url to share with:
<form action="/addshare" method="post"><input type="text" size="40" name="url"> 
<br>
Aspects: 
{repeat TAGS}
<input type="checkbox" name="#TAGNAME#" value="1"> #TAGNAME#
{end}
<br>
New aspects (comma separated): <input type="text" name="newtags">
<br>
<input type="submit"></form>
<h2>Existing Shares</h2>
<table border="1">
<tr>
<th>Name</th><th>URL</th><th>Aspects</th><th></th>
</tr>
{repeat SHARES}
<tr>
<td>#SNAME#</td><td>#URL#</td><td>#TAGS#</td><td><form action="/unshare" method="post"><input type="hidden" name="url" value="#URL#"><input type="submit" value="unshare"></form></td>
</tr>

{end}
</table>
</div>
