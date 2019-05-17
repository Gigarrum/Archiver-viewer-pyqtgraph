#!/usr/bin/python
# -*- coding: utf-8 -*-

#Developer: Paulo Baraldi Mausbach
#LNLS - Brazilian Synchrotron Light Source Laboratory

import requests
import os
import datetime

class ArchiverRequester():
    def __init__(self,protocol,ip,port):

        self.requestPrefix = protocol + "://" + ip + ":" + port + "/retrieval/data/getData.json?"

    #Recives a datetime.datime atribute and encode it for being compatible on url request
    def encodeDateISO8601(self,datetime,tz = 'Z'):

        datetime = datetime.isoformat() + tz
        return datetime

    def requestHistoricalData(self,pvName,startTime = None,endTime = None,tz = 'Z'):

        #Check which kind of request will be done

        #Assemble Request url for data "from datetime to NOW"
        if(endTime == None and startTime != None):

            #Encode start time for compatible datetime pattern
            startTime = self.encodeDateISO8601(startTime,tz)

            apiRequest = "pv=" + pvName + "&from=" + startTime

        #Assemble Request url for data "from datetime to datetime"
        elif(endTime != None and startTime != None):

            #Encode start and end time for compatible datetime pattern
            startTime = self.encodeDateISO8601(startTime,tz)
            endTime = self.encodeDateISO8601(endTime,tz)

            apiRequest = "pv=" + pvName + "&from=" + startTime + "&to=" + endTime
        else:
            print("Invalid datetime interval!!!")

        #Finish assemble of request Url
        requestUrl = self.requestPrefix + apiRequest

        print(requestUrl)#[DEBUG]

        #Make request
        r = requests.get(requestUrl)  # blocking.  BAD!
        if r.status_code == 200 and r.headers['content-type'] == 'application/json':
            data_dict = r.json()
            return data_dict
        else:
            return None
        #print(data_dict)#[DEBUG]
