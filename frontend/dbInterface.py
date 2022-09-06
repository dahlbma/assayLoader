import requests
import json

baseUrl = 'http://esox3.scilifelab.se:8084/'

def listify(data, addBlank=True):
    res = data.content.decode()
    res = json.loads(res)
    cleanList = list()
    if addBlank:
        cleanList.append(' ')
    for i in res:
        cleanList.append(i[0])
    return cleanList

def login(user, password, database):
    r = requests.post(f'{baseUrl}login',
                      data = {'username':user,
                              'password':password,
                              'database':database})
    return r

def getDatabase():
    r = requests.get(f'{baseUrl}getDatabase')
    res = listify(r, False)
    return res

def uploadBinary(token, os_name, file):
    r = requests.post(f'{baseUrl}uploadBinary',
                      data = {'os_name':os_name},
                      headers = {'token':token},
                      files = {'file':file})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getAssayLoaderBinary(os_name):
    r = requests.get(f'{baseUrl}getAssayLoaderBinary/{os_name}',
                     stream=True) #fetch assayLoader dist
    return r

def getVersion():
    r = requests.get(f'{baseUrl}getVersionData') #get file version
    return r

def uploadVersionNo(token, ver_no):
    r = requests.post(f'{baseUrl}uploadVersionNo',
                      data = {'ver_no':ver_no},
                      headers = {'token':token}) #get file version
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def uploadLauncher(token, os_name, file):
    r = requests.post(f'{baseUrl}uploadLauncher',
                      data = {'os_name':os_name},
                      headers = {'token':token},
                      files = {'file':file})
    if r.status_code != 200:
        return r.content.decode(), False
    else:
        return r.content.decode(), True

def getProjects(token):
    r = requests.get(f'{baseUrl}getProjects',
            headers={'token':token})

    cleanList = listify(r, False)
    return cleanList

def getTargets(token):
    r = requests.get(f'{baseUrl}getTargets',
            headers={'token':token})

    cleanList = listify(r, False)
    return cleanList

def getAssayTypes(token):
    r = requests.get(f'{baseUrl}getAssayTypes',
            headers={'token':token})
    cleanList = listify(r, False)
    return cleanList

def getDetectionTypes(token):
    r = requests.get(f'{baseUrl}getDetectionTypes',
            headers={'token':token})
    cleanList = listify(r, False)
    return cleanList

def getOperators(token):
    r = requests.get(f'{baseUrl}getOperators',
            headers={'token':token})
    cleanList = listify(r, False)
    return cleanList

def getSinglePointConfig(token):
    r = requests.get(f'{baseUrl}getSinglePointConfig',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content

def getDoseResponseConfig(token):
    r = requests.get(f'{baseUrl}getDoseResponseConfig',
            headers={'token':token})
    try:
        return r.content.decode()
    except:
        return r.content
