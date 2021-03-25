# bugsplat 接口文档 url: https://www.bugsplat.com/docs/api/webservices-api/
# 此脚本用于下载bugsplat上的dump文件

import requests
import json
import os


# 登录用户名和密码
bugsplat_email = ""
bugsplat_password = ""

bugsplat_database = "filme_imyfone_com"

# 可以根据版本号和时间段进行下载
bugsplat_version = "win3.2.1.13"
bugsplat_starttime = "2021-03-25:00:00:00"
bugsplat_endtime = "2021-03-26:00:00:00"

# dump 下载保存路径
outputPath = "D:\\"
outputPath += "busplat_" + bugsplat_version + "_" + bugsplat_starttime.replace(":", "-") + "_" + bugsplat_endtime.replace(":", "-")

# 下载失败列表
downloadFailedDict = {}


def mkdir(path):
	folder = os.path.exists(path)
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)              #makedirs 创建文件时如果路径不存在会创建这个路径

def download_file(url, saveFile):
  i = 0
  while i < 3:
    try:
      myfile = requests.get(url, timeout=60)
      open(saveFile, 'wb').write(myfile.content)
      return True
    except requests.exceptions.RequestException as e:
      print(e)
      i += 1
  return False


def bugsplat_auth(email, password):
  url = "https://app.bugsplat.com/api/authenticatev3"
  payload={
    'email': email,
    'password': password
  }

  try:
    response = requests.request("POST", url, data=payload, timeout=30)
    print("[bugsplat_auth] status_code = ", response.status_code)
    
    if not json.loads(response.text)["authenticated"]:
      return ""
    return response.headers["Set-Cookie"]
  except requests.exceptions.RequestException as e:
    print(e)
    return ""



def bugsplat_allcrash(cookie):
  url = "https://app.bugsplat.com/allCrash"
  params = (
      ('database', bugsplat_database),
      ('pagesize', '500'),
      ('filterscount', '3'),
      ('filterdatafield0', 'appVersion'),
      ('filtercondition0', 'EQUAL'),
      ('filtervalue0', bugsplat_version),
      ('filteroperator1', 'AND'),
      ('filterdatafield1', 'crashTime'),
      ('filtercondition1', 'GREATER_THAN'),
      ('filtervalue1', bugsplat_starttime),
      ('filteroperator2', 'AND'),
      ('filterdatafield2', 'crashTime'),
      ('filtercondition2', 'LESS_THAN'),
      ('filtervalue2', bugsplat_endtime),
  )
  headers = {
    'Cookie': cookie
  }

  try:
    response = requests.request("GET", url, params=params, headers=headers, timeout=30)
    print("[bugsplat_allcrash] status_code = ", response.status_code)
    return response.text
  except requests.exceptions.RequestException as e:
    print(e)
    return ""

def bugsplat_crashdata(cookie, id):
  url = "https://app.bugsplat.com/api/crash/data"
  params = (
      ('database', bugsplat_database),
      ('id', id)
  )
  headers = {
    'Cookie': cookie
  }
  try:
    response = requests.request("GET", url, headers=headers, params=params, timeout=30)
    print("[bugsplat_crashdata] status_code = ", response.status_code)
    return response.text
  except requests.exceptions.RequestException as e:
    print(e)
    return ""


cookie = bugsplat_auth(bugsplat_email, bugsplat_password)
if cookie == "":
  exit(-1)

allcrash = bugsplat_allcrash(cookie)
if allcrash == "":
  exit(-1)

allcrashJson = json.loads(allcrash)
mkdir(outputPath)
with open(outputPath + "\\bugsplat.json", 'w', encoding='utf-8') as f1:
   f1.write(json.dumps(allcrashJson, indent=4, ensure_ascii=False))

for item in allcrashJson[0:]:
  if item["Database"] != bugsplat_database:
    continue
  rows = item["Rows"]

  i = 0
  count = len(rows)
  for row in rows[0:]:
    i += 1
    stackKey = row["stackKey"]
    id = row["id"]
    if not stackKey or not id:
      print("(%d/%d) stackKey or id is null." % (i, count))
      continue

    crashdata = bugsplat_crashdata(cookie, id)
    if crashdata == "":
      print("(%d/%d) crashdata is empty. id = (%d)" % (i, count, id))
      continue

    crashdataJson = json.loads(crashdata)
    dumpUrl = crashdataJson["dumpfile"]
    if dumpUrl == "":
      print("(%d/%d) dumpUrl is empty. id = (%d)" % (i, count, id))
      continue
    
    dumpPath = outputPath + "\\" + stackKey + "\\" + id
    print("create dir: " + dumpPath)
    mkdir(dumpPath)

    tmp = dumpUrl.split("?")[0]
    dumpFileName = tmp.split("/")[-1]

    if os.path.exists(dumpPath + "\\" + dumpFileName):
      print("(%d/%d) film exists: (%s)" % (i, count, dumpPath + "\\" + dumpFileName))
      continue

    print("dump film name: " + dumpFileName)
    print("******(%d/%d) starting download, file: %s" % (i, count, dumpUrl))

    if download_file(dumpUrl, dumpPath + "\\" + dumpFileName): 
      print("****** download successful.")
    else:
      print("****** download failed.")
      downloadFailedDict[dumpPath] = dumpUrl
    print("\r\n")

if len(downloadFailedDict) != 0:
  print(downloadFailedDict)

print("done!")
