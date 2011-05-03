{parent mainlayout.tpl}

<div style="position:relative; left:100px;">
<b>Edit profile information</b>
<form action="/saveprofile" method="post">
Name: <input type="text" name="name" value="#NAME#"> 
<br>
E-Mail: <input type="text" name="email" value="#EMAIL#"> 
<br>
<input type="submit"></form>
<p>

<b>URLs under which your public stream can be accessed</b>
<div style="font-face: Arial, Helvetica, sans-serif; font-size:12pt;">
Add a new URL:
<form action="/addalturl" method="post"><input type="text" name="url"> 
<br>
<input type="submit"></form>
<b>Alternative URLS</b>:<p>
<ul>{repeat ALTURLS}
<li>
<form action="/removealturl" method="post">#URL# <input type="hidden" name="url" value="#URL#"><input type="submit" value="remove"></form><br>

{end}
</ul></div>
