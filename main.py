import requests
from bs4 import BeautifulSoup
import sqlite3 as sql
import json
import os.path

indexprocessurl = "http://202.166.205.141/bbvrs/index_process.php"
databaseName = "Voterlist.db"
progressFilename = "Progress.json"
masterDict={}

def createTableIfNotExists(dbName):
    conn=sql.connect(dbName)
    CREATETABLEQUERY="create table if not exists AllVoters (VoterId int primary key not null, VoterName text not null, " \
                     "Sex text not null, FatherName text not null, MotherName text not null, District text not null, " \
                     "DistrictCode int not null, VDC_Mun text not null, VDC_MunCode int not null, Ward int not null, " \
                     "PollingBooth text not null, PollingBoothCode int not null)"
    conn.execute(CREATETABLEQUERY)
    conn.commit()
    conn.close()

def saveProgress(i,vdc_index,ward_index,booth_index):
    savedict={"DistrictIndex":i,"VDCIndex":vdc_index,"WardIndex":ward_index,"BoothIndex":booth_index}
    with open("Progress.json","w") as progfile:
        json.dump(savedict,progfile)

def populateVoters_Into_DB(dbName):
    createTableIfNotExists(dbName)

    loaded_district_index=1
    loaded_vdc_index=0
    loaded_ward_index=0
    loaded_booth_index=0
    if os.path.exists(progressFilename):
        if os.path.isfile(progressFilename):
            with open(progressFilename,"r") as pfile:
                savedstatedict=json.load(pfile)
            loaded_district_index=savedstatedict["DistrictIndex"]
            loaded_vdc_index=savedstatedict["VDCIndex"]
            loaded_ward_index=savedstatedict["WardIndex"]
            loaded_booth_index=savedstatedict["BoothIndex"]

    url = "http://202.166.205.141/bbvrs/view_ward.php"
    data = {"district": 0, "vdc_mun": 0, "ward": 0, "reg_centre": 0}

    i = loaded_district_index
    vdc_index=loaded_vdc_index
    ward_index=loaded_ward_index
    booth_index=loaded_booth_index

    while i < 76:
        data["district"] = i
        districtname=masterDict[str(i)]["Name"]
        while vdc_index < len(masterDict[str(i)]["VDCs"]):
            data["vdc_mun"] = list(masterDict[str(i)]["VDCs"][vdc_index])[0]
            vdcname=masterDict[str(i)]["VDCs"][vdc_index][data["vdc_mun"]]
            with requests.session() as session:
                while ward_index < len(masterDict[str(i)]["VDCs"][vdc_index]["Wards"]):
                    sqlconnection = sql.connect(databaseName)
                    data["ward"] = list(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index])[0]
                    while booth_index < len(
                            masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"]):
                        data["reg_centre"] = list(
                            masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"][
                                booth_index])[0]
                        boothname=masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"][
                                booth_index][data["reg_centre"]]
                        response = session.post(url,data=data).text
                        soup = BeautifulSoup(response)
                        insidediv = soup.find("div", attrs={"class": "div_bbvrs_data"})
                        tbody = insidediv.find("tbody")
                        tr = tbody.find_all("tr")
                        for row in tr:
                            td = row.find_all("td")
                            sno = int(td[0].text)
                            voterId = int((td[1].text).replace(" ",""))
                            votername = td[2].text
                            sex = td[3].text
                            fathersname = td[4].text
                            mothersname = td[5].text
                            sqlconnection.execute(
                                "insert or ignore into AllVoters values (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (voterId, votername, sex, fathersname, mothersname, districtname, i, vdcname,
                                int(data["vdc_mun"]), int(data["ward"]), boothname, int(data["reg_centre"])))
                        sqlconnection.commit()
                        print("Indices of : District {}/75 VDC {}/{} Ward {}/{} Booth {}/{}".format(
                            i,vdc_index+1,len(masterDict[str(i)]["VDCs"]),ward_index+1,len(masterDict[str(i)]["VDCs"][vdc_index]["Wards"]),
                            booth_index+1,len(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"])))
                        saveProgress(i, vdc_index, ward_index, booth_index)  # saves progressed indices to a progress file
                        booth_index+=1
                    booth_index=0
                    sqlconnection.close()
                    print("SQL connection closed")
                    ward_index+=1
                ward_index=0
            vdc_index+=1
        vdc_index=0
        i+=1




def populateVoters_Into_masterDict():
    url="http://202.166.205.141/bbvrs/view_ward.php"
    data = {"district": 0, "vdc_mun": 0, "ward": 0, "reg_centre": 0}

    for i in range(1,76):
        data["district"]=i
        for vdc_index in range(len(masterDict[str(i)]["VDCs"])):
            data["vdc_mun"] = list(masterDict[str(i)]["VDCs"][vdc_index])[0]
            for ward_index in range(len(masterDict[str(i)]["VDCs"][vdc_index]["Wards"])):
                data["ward"] = list(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index])[0]
                for booth_index in range(len(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"])):
                    data["reg_centre"]=list(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"][booth_index])[0]
                    masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"][booth_index]["Voters"]=[]
                    response = requests.post(url, data=data).text
                    soup = BeautifulSoup(response)
                    insidediv = soup.find("div", attrs={"class": "div_bbvrs_data"})
                    tbody = insidediv.find("tbody")
                    tr = tbody.find_all("tr")
                    for row in tr:
                        td = row.find_all("td")
                        sno=td[0].text
                        voterId=td[1].text
                        votername=td[2].text
                        sex=td[3].text
                        fathersname=td[4].text
                        mothersname=td[5].text
                        masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][str(data["ward"])]["PollBooths"][
                            booth_index]["Voters"].append(
                            {"SN": sno, "VoterId": voterId, "Name": votername, "Sex": sex, "Father's Name": fathersname,
                             "Mother's Name": mothersname})


def populateBooths():
    data={"vdc":0,"ward":0,"list_type":"reg_centre"}

    for i in range(1,76):
        for vdc_index in range(len(masterDict[str(i)]["VDCs"])):
            data["vdc"] = list(masterDict[str(i)]["VDCs"][vdc_index])[0]
            for ward_index in range(len(masterDict[str(i)]["VDCs"][vdc_index]["Wards"])):
                data["ward"] = list(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index])[0]
                response = requests.post(indexprocessurl, data=data)
                jsonresponse = response.json()
                result = jsonresponse["result"]
                soup = BeautifulSoup(result)
                options = soup.find_all("option")
                firstoption = True
                for option in options:
                    if not firstoption:
                        boothId=option.attrs["value"]
                        boothName=option.text
                        strWardnumber=list(masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index])[0]
                        masterDict[str(i)]["VDCs"][vdc_index]["Wards"][ward_index][strWardnumber]["PollBooths"].append({boothId:boothName})
                    else:
                        firstoption=False


def populateWards():
    data = {"vdc": 0, "list_type": "ward"}

    for i in range(1,76):
        for index in range(len(masterDict[str(i)]["VDCs"])):
            masterDict[str(i)]["VDCs"][index]["Wards"]=[]
            data["vdc"]=list(masterDict[str(i)]["VDCs"][index])[0]
            response=requests.post(indexprocessurl,data=data)
            jsonresponse=response.json()
            result=jsonresponse["result"]
            soup=BeautifulSoup(result)
            options=soup.find_all("option")
            firstoption=True
            for option in options:
                if not firstoption:
                    wardNo=option.attrs["value"]
                    masterDict[str(i)]["VDCs"][index]["Wards"].append({wardNo:{"PollBooths":[]}})
                else:
                    firstoption=False


def populateVDCs():
    data={"district":0,"list_type":"vdc"}

    # get all vdc's
    for i in range(1,76):   # district id
        data["district"]=i
        response=requests.post(indexprocessurl,data=data)
        jsonresponse=response.json()
        result=jsonresponse["result"]
        soup=BeautifulSoup(result)
        options=soup.find_all("option")
        firstoption=True
        masterDict[str(i)]["VDCs"]=[]
        for option in options:
            if not firstoption:
                vdcId=option.attrs["value"]
                vdcName=option.text
                masterDict[str(i)]["VDCs"].append({vdcId:vdcName})
            else:
                firstoption=False


def populateDistrictDictionary():
    rooturl="http://202.166.205.141/bbvrs/index.php"
    responsetext=requests.get(rooturl).text
    soup=BeautifulSoup(responsetext)
    s=soup.find(id="district")
    options=s.find_all("option")
    first=True
    for option in options:
        if not first:
            districtId=option.attrs["value"]
            districtName=option.text
            masterDict[districtId]={"Name":districtName}
        else:
            first=False


populateDistrictDictionary()
populateVDCs()
populateWards()
populateBooths()
# with open("uptopollbooth.txt","r",encoding="utf-8") as file:
#     masterDict=eval(file.read())
populateVoters_Into_DB(databaseName)
print("end")
