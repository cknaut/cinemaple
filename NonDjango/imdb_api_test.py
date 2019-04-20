''' Testing OMD API '''
import urllib, json 

imdbid = "tt0133093"
OMDAPI = "274350fc"

args = {"apikey": OMDAPI, "i": imdbid, "plot" : "full"}

url_api = " http://www.omdbapi.com/?{}".format(urllib.parse.urlencode(args))

with urllib.request.urlopen(url_api) as url:
    data = json.loads(url.read().decode())

title = data["Title"]

title = data["Title"]
