{parent mainlayout.tpl}
<h2>Wall for #NAME#</h2>
<div style="position:relative; left:100px;">
<div style="font-face: Arial, Helvetica, sans-serif; font-size:12pt;">
What are you doing?
<form action="/poststatus" method="post"><input type="text" size="120" name="status"> 
<br>
Aspects: 
{repeat TAGS}
<input type="checkbox" name="#TAGNAME#" value="1"> #TAGNAME#
{end}
<br>
<input type="checkbox" name="sharepublic" value="public"> Share publicly.
<br>
<input type="submit"></form>
<hr noshade>
Please refresh the wall manually. Posts take a long time to load for now.
<p>
{repeat POSTS}
<div style="background-color:#CCCCFF; padding:2px; margin: 2px;">#PNAME# said: #PTEXT#<br>
<span style="font-size:8pt;">#DT#</span>
</div>

{end}
</div>
