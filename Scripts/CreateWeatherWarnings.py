'''-------------DISCLAIMER---------------------------------------------------
All rights reserved under the copyright laws of the United States.

You may freely redistribute and use this sample code, with or without modification.  The sample code is provided 
without any technical support or updates.

Disclaimer OF Warranty: THE SAMPLE CODE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING THE 
IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NONINFRINGEMENT ARE DISCLAIMED. IN NO 
EVENT SHALL 
ESRI OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) SUSTAINED BY YOU OR A THIRD PARTY, HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
LIABILITY, OR TORT ARISING IN ANY WAY OUT OF THE USE OF THIS SAMPLE CODE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  
THESE LIMITATIONS SHALL APPLY NOTWITHSTANDING ANY FAILURE OF ESSENTIAL PURPOSE OF ANY LIMITED REMEDY.

For additional information contact: Environmental Systems Research Institute, Inc.
Attn: Contracts Dept.
380 New York Street
Redlands, California, U.S.A. 92373 
Email: contracts@esri.com
---------------------------------------------------------------------------'''

#Required Python Packages
import arcpy
from BeautifulSoup import BeautifulSoup
import os
import urllib
from arcpy import env
import datetime
import time

scratchWS = env.scratchWorkspace;
if scratchWS == None:
    scratchWS = r'C:\ArcGISData\FedCON2014\EffectiveProgramming\Workspace' #'E:\ArcGISFWeather\Nexrad\scratch' 
    
countyPolygonDataset = "Counties"
nwsAlerts = "NWSAlerts"
connectionString = ""

## Code for connecting to the database
def connectToDatabase(databaseName,connectionName):
    # Provide connection information
    # http://resources.arcgis.com/en/help/main/10.2/index.html#//00170000016q000000
    
    instance = "mycomputername"  
    database = databaseName 
    user = 'GISDataOwner'
    password = 'mypassword'
            
    Connection_File_Name = scratchWS + "\\" + connectionName + ".sde"
        
    arcpy.AddMessage("Creating ArcSDE Connection File...")
    #arcpy.CreateDatabaseConnection_management(scratchWS, "connection.sde","SQL_SERVER",instance,"OPERATING_SYSTEM_AUTH","#","#","SAVE_USERNAME",database,"#","POINT_IN_TIME","#","#")    
    arcpy.CreateDatabaseConnection_management(scratchWS, "connection.sde","SQL_SERVER",instance,"DATABASE_AUTH",user,password ,"SAVE_USERNAME",database,"#","POINT_IN_TIME","#","#")    

    
    return Connection_File_Name

## Deletes Old Features
def removeOldFeatures():
    #http://resources.arcgis.com/en/help/main/10.2/index.html#//001700000036000000
    fc = connectionString + "/DCDevSummit.GISDATAOWNER.Weather"
    arcpy.DeleteFeatures_management(fc)
    return 1


def addDataToFeatureClass(alerts):
    #Using the data access module we populate the feature class with new data
    #Using insert cursor to add new record
    for warning in alerts:

        if not len(warning['Geocode']['value']) < 1: # Check to make sure there are FIPS codes.    
            fipsCount = 0
            selectExp = ''
            for fips in warning['Geocode']['value']:
                shape = getCountyPolygons(fips[1:])
                if(shape != []):
                    insertNewRecords(shape,warning)
    return 0


## Uses Insert Cursor to add new features
def insertNewRecords(shapeValue,warningInfo):
    #http://resources.arcgis.com/en/help/main/10.2/index.html#/InsertCursor/018w0000000t000000/
    fc = connectionString + "/DCDevSummit.GISDATAOWNER.Weather"
    arcpy.env.workspace = connectionString;

    
    rows = arcpy.InsertCursor(fc)
    row = rows.newRow()
    row.setValue("shape", shapeValue)
    row.setValue("EVENT", warningInfo['Type'])
    row.setValue("CATEGORY", warningInfo['Category'])
    row.setValue("URGENCY", warningInfo['Urgency'])
    row.setValue("SEVERITY", warningInfo['Severity'])
    row.setValue("CERTAINTY", warningInfo['Certainty'])
    row.setValue("UTC_START", warningInfo['Published'])
    row.setValue("UTC_END", warningInfo['Expires'])
    row.setValue("INC_DESC", warningInfo['Title'])
    rows.insertRow(row)    

## Uses da Search Cursor to get County Polygon    
def getCountyPolygons(fips):
    #http://resources.arcgis.com/en/help/main/10.2/index.html#//018w00000011000000
    fipsQuery = "FIPS = \'" + fips + '\''
    fc = connectionString + "/DCDevSummit.GISDATAOWNER.USCounties"
    fields = ["FIPS", "NAME", "SHAPE@"]    
    shape = [];
    with arcpy.da.SearchCursor(fc, fields,fipsQuery) as cursor:
        for row in cursor:
            print(row[0])    
            shape = row[2]; #break
    #Use search cursor to get polygon from feature class.
    #http://resources.arcgis.com/en/help/main/10.2/index.html#//018w00000011000000
    
    return shape

def makeTime(timeStamp):
    localUtcOffset = 4 
    utcOffset = int(str(timeStamp[-6:]).replace(r':', ''))/100
    localTime = time.strptime(timeStamp[:-6], '%Y-%m-%dT%H:%M:%S')
    timeValue = time.mktime(localTime) - ((utcOffset + localUtcOffset) * 60 * 60)
    timeValue = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeValue))
    return timeValue

def getAlerts():
    sendURL = r'http://alerts.weather.gov/cap/us.php?x=1'
    returnXML = urllib.urlopen(sendURL).read()
    # Replace the tags containing 'cap:' so that they can be easily referenced by BeautifulSoup.
    cleanedXML = str(returnXML).replace(r'cap:', 'CAP')
    
    parsed = BeautifulSoup(cleanedXML)    
    
    alertsList = []
    
    # Build a list of the entries and attributes for use in creating a feature class.
    entries = parsed.findAll('entry')
    for entry in entries:        
        alertDic = {}
        alertDic['Url'] = entry.idTag.string
        alertDic['Updated'] = makeTime(entry.updatedTag.string)
        alertDic['Published'] = makeTime(entry.publishedTag.string)
        alertDic['Author'] = entry.authorTag.nameTag.string   
        alertDic['Title'] = entry.titleTag.string
        alertPosition = alertDic['Title'].find('issued') # find position of the word 'issued'
        alertDic['Type'] = alertDic['Title'].string[:(alertPosition - 1)] # grab everything to the left of ' issued'

        try:
            alertDic['Summary'] = entry.summaryTag.string[:255]
        except:
            alertDic['Summary'] = ''

        alertDic['Effective'] = makeTime(entry.capeffectiveTag.string)
        alertDic['Expires'] = makeTime(entry.capexpiresTag.string)
        alertDic['Status'] = entry.capstatusTag.string
        alertDic['Category'] = entry.capcategoryTag.string
        alertDic['Urgency'] = entry.capurgencyTag.string
        alertDic['Severity'] = entry.capseverityTag.string
        alertDic['Certainty'] = entry.capcertaintyTag.string
        geocodeDic = {}
        geocodeDic['name'] = entry.capgeocodeTag.valuenameTag.string
        if not entry.capgeocodeTag.valueTag.string == None:
            geocodeDic['value'] = entry.capgeocodeTag.valueTag.string.split(' ')
        else:
            geocodeDic['value'] = ''
        alertDic['Geocode'] = geocodeDic
        parameterDic = {}
        parameterDic['name'] = entry.capparameterTag.valuenameTag.string
        parameterDicValue = entry.capparameterTag.valueTag.string
        if not parameterDicValue == None:
            parameterDic['value'] = parameterDicValue.split(r'//')
        else:
            parameterDic['value'] = ''
        alertDic['Parameter'] = parameterDic
        
        # Append the entry dictionary to alertsList.
        alertsList.append(alertDic)
        
    arcpy.AddMessage('Collected ' + str(len(alertsList)) + ' weather statements.')
    return alertsList;

def synChanges():
    #http://resources.arcgis.com/en/help/main/10.2/index.html#//00170000001s000000
    replicaDB = connectToDatabase(DCDevSummitProd,'replicaDB');
    arcpy.SynchronizeChanges_management("MySDEdata.sde", "My2wayReplica", "MySDEdata_child.sde", "BOTH_DIRECTIONS", \
    "IN_FAVOR_OF_GDB1", "BY_ATTRIBUTE", "")    

def dataCleanup():
    try:
        arcpy.AddMessage("Data Clean Up...")
        folder = scratchWS
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception, e:
                print e
                
        arcpy.AddMessage("Data Clean Up Finished")
        
    except:
        arcpy.AddMessage("Data Clean Up Failed")        
        print arcpy.GetMessages()  


#CONNECT TO STAGING DATABASE        
connectionString = connectToDatabase("DCDevSummit",'connection'); 

#DELETE ALL THE FEATURES IN STAGING
removeOldFeatures();

#GET WEATHER WARNING AND ALERTS
alerts = getAlerts();

#INSERT WEATHER ALERTS INTO STAGING DATABASE FEATURE CLASS
addDataToFeatureClass(alerts)

#SYNCHRONIZE STAGING WITH PRODUCTION GEODATABASE
#synChanges():

#REMOVE ALL TEMPORARY FILES
dataCleanup()

print "Done Script"