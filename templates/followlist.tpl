{parent mainlayout.tpl}
<h2>Feeds which #NAME# follows</h2>
<div style="position:relative; left:100px;">
<div style="font-face: Arial, Helvetica, sans-serif; font-size:12pt;">
Add a new url to follow:
<form action="/addfollow" method="post"><input type="text" size="40" name="url"> 
<br>
<input type="submit"></form>
<h2>Feeds you follow</h2>
<table border="1">
<tr>
<th>Name</th><th>URL</th><th></th>
</tr>
{repeat FOLLOWS}
<tr>
<td>#FNAME#</td><td>#URL#</td><td><form action="/unfollow" method="post"><input type="hidden" name="url" value="#URL#"><input type="submit" value="unfollow"></form></td>
</tr>

{end}
</table>
</div>
