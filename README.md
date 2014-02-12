# Effective Database Programming Workshop

This repository has example code for the effective database programming workshop at the Esri DC Developer Conference on 2/2/2014



## Steps
###Connect to Staging Database
###Remove Old Features
###Get Alerts
###Get Counties Associated with Alert
###Insert Alerts\Counties into Feature Class
###Synch Changes with Replicated Database
###Clean up workspace

## Pseudo Code
###ConnectToStaggingDB()
###DeleteOldRecords()
###GetAlerts()
###AddAlertsToFeatureClass ( alerts )
	####For each alert
		#####For each County
			######GetCountyShape ( FIPS )
			######InsertRecord ( alert, shape )
###SynchChanges()
	####ConnectToProductionDatabase()
	####SynchtonizeChanges()
###DataCleanUp()



## Licensing
Copyright 2012 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [license.txt](https://raw.github.com/kevinsigwart/AGOL_MultiDimTemplate/master/license.txt) file.

[](Esri Language: JavaScript)

