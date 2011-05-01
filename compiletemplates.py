#!/env/python
#    This file is part of autono:me - a set of tools to manipulate encrypted 
#    social networking files
#    (C) 2011, by its creators
#
#    autono:me is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    autono:me is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with autono:me. If not, see <http://www.gnu.org/licenses/>.
import os

html_files = filter(lambda x: x.endswith('.tpl'), os.listdir('templates'))

print "def get_template(name):"
for i in html_files:
	f = open("templates"+os.sep+i,"r")
	c = f.read()
	f.close()
	print "\tif name == \""+i+"\":"
	print "\t\treturn \"\"\"" + c + "\"\"\""

