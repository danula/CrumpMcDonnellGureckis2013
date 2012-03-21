# -*- coding: utf-8 -*-
# <nbformat>3</nbformat>

# <headingcell level=1>

# ...:::''' Active Learning of Logical Rules (Utilities) ''':::...

# <markdowncell>

# Project by John McDonnell, Devin Domingo, Todd Gureckis
# 
# This notebook provides basic functions which are useful for data analysis.
# 
# *Version 1.0 - Todd Gureckis*

# <headingcell level=1>

# Stuff for accessing the database and reformatting the data

# <codecell>

#from sqlalchemy import *

#-----------------------------------------------------
# connect_to_database - loads and forms connection
#-----------------------------------------------------
def connect_to_database(databaseurl, table):
    engine = create_engine(databaseurl, echo=False)
    metadata = MetaData()
    metadata.bind = engine
    db = load_database(engine, metadata, table)
    conn = engine.connect()
    return db, conn

#-----------------------------------------------------
# load_database - loads database schema
#-----------------------------------------------------
def load_database(engine, metadata, tablename):
    try:
        participants = Table(tablename, metadata, autoload=True)
    except:
        print "Error, participants table doesn't exist"
        exit()
    return participants

#-----------------------------------------------------
# get_people - gets individual records as a dictionary
#-----------------------------------------------------
def get_people(conn, s):
    people={}
    i=0
    for row in conn.execute(s):
        person = {}
        for field in ['subjid', 'ipaddress', 'hitid', 'assignmentid', 'workerid',
                        'cond', 'counterbalance', 'beginhit','beginexp', 'endhit',
                        'status', 'codeversion', 'datafile']:
            if field=='datafile':
                if row[field] == None:
                    person[field] = "Nothing yet"
                else:
                    person[field] = row[field]
            else:
                person[field] = row[field]
        people[i] = person
        i+=1
    return people

# <headingcell level=1>

# Misc stuff

# <codecell>

def count_longest_run(values):
    current_value = values[0]
    runs = []
    current_run = []
    current_run.append(values[0])
    for i in range(1,len(values)):
        if current_value == values[i]:
            current_run.append(values[i])
        else:
            current_value = values[i]
            runs.append(current_run)
            current_run = [current_value]
    lens = [len(i) for i in runs]
    return max(lens)

# <headingcell level=1>

# A "Participant" class.  Encapsulates all we know about a particular subject.

# <markdowncell>

# Any measure you want to use to describe individuals could be added as a method to this class, then added to the constructor (__init__).

# <codecell>

#from pandas import *
#from string import replace

TEST = '1'
TRAINING = '2'
INSTRUCT = '3'
TRUE = '0'
FALSE = '1'
stimuliperblock = 16.

#-----------------------------------------------------
# Participant - a class for manipulation subject data
#-----------------------------------------------------
class Participant():
    def __init__(self, record, process=True):
        # process person here
        for field in record.keys():
            if field in ['subjid','cond','counterbalance','status']:
                vars(self)[field] = int(record[field])
            else:
                vars(self)[field] = record[field]
        self.datafileorig = self.datafile[:]
        self.format_datafile_as_list()
        self.format_datafile_as_dataframe()
        if process==True:
            self.blocks_to_criterion()
            self.per_block_learning_curve()
            self.medianRT()
            self.maxRT()
            self.meanOverallAcc()
            self.percentLongRT()
            self.get_questionaire()
        self.get_conditions()
        
        
    def __getitem__(self,field):
        return vars(self)[field]
    
    def format_datafile_as_list(self):
        # this junk is just required to make the data file more ammendable to analysis
        # replace word 'true' and 'false' with numbers
        #print self.datafileorig
        self.datafile = replace(self.datafile, 'true', TRUE)
        self.datafile = replace(self.datafile, 'false', FALSE)
        # replace words 'TRAINING' and 'TEST' with codes
        self.datafile = replace(self.datafile, 'TEST', TEST)
        self.datafile = replace(self.datafile, 'TRAINING', TRAINING)
        self.datafile = replace(self.datafile, 'INSTRUCT', INSTRUCT)
        if self.datafile[-1:]=='\r\n':
            self.datafileF = self.datafile.split('\r\n')
        else:
            self.datafileF = self.datafile.split('\n')
        
        res = []
        for line in self.datafileF:
            tmp = line.split(',')
            res.append(tmp)
        self.datafileF = res
        self.datafileFInstruct = []
        self.datafileFTraining = []
        self.datafileFTest = []
        
        for line in self.datafileF:
            if len(line)>8:
                if line[7]==TRAINING:
                    newline = []
                    for item in range(len(line)):
                        if item not in [12,13]:
                            newline.append(int(line[item]))
                        else:
                            newline.append(line[item])
                    self.datafileFTraining.append(newline)
                elif line[7]==TEST:
                    #for item in line:
                    #    print int(item)
                    newline = map(int, line)
                    self.datafileFTest.append(newline)
            elif len(line)==8:
                if line[5]==INSTRUCT:
                    newline = line[:]
                    self.datafileFInstruct.append(newline)

    def get_conditions(self):
        self.subjid = int(self.datafileFInstruct[0][0])
        self.traintype = int(self.datafileFInstruct[0][1])
        self.rule = int(self.datafileFInstruct[0][2])
        
    def get_questionaire(self):
        tmpstr = self.datafileorig.split('\r\n')
        res = []
        for line in tmpstr:
            tmp = line.split(',')
            res.append(tmp)
        for line in tmpstr:
            if line[:3] in ['rul', 'how', 'eng', 'dif', 'phy','edu','gen','age'] or line[:1] in [":"]:
                qa = line.split(':')
                #print self.subjid, line, qa
                if line[:1] == ":":
                    #print self.subjid, line
                    vars(self)["physicalaids"]=line[1:]  
                elif line[:3] in ['eng', 'dif', 'age']:
                    vars(self)[qa[0]] = int(qa[1])
                else:
                   vars(self)[qa[0]] = qa[1]

    
    def format_datafile_as_dataframe(self):
        if not self.datafileFInstruct:
            #print "run format_datafile_as_list first!"
            pass
        else:
            self.dfInstruct = DataFrame(self.datafileFInstruct, columns=['subjid', 'traintype', 'rule', \
                                                                        'dimorder', 'dimvals', 'type', 'file', \
                                                                        'rt'])
        
        if not self.datafileFTraining:
            #print "run format_datafile_as_list first!"
            pass
        else:
            self.dfTraining = DataFrame(self.datafileFTraining, columns=['subjid', 'traintype', 'rule', \
                                                                        'dimorder', 'dimvals', 'block', \
                                                                        'trial', 'type', 'theorystim', \
                                                                        'actualstim', 'category','loc', 'shuffleTheory', \
                                                                        'shuffleActual', 'rt'])
        if not self.datafileFTest:
            #print "run format_datafile_as_list first!"
            pass
        else:
            self.dfTest = DataFrame(self.datafileFTest, columns=['subjid', 'traintype', 'rule', \
                                                                        'dimorder', 'dimvals', 'block', \
                                                                        'trial', 'type', 'theorystim', \
                                                                        'actualstim', 'correct','resp', 'hit', 'rt'])

    def blocks_to_criterion(self):
        self.nBlocksToCriterion = self.dfTest['block'].max()

    def percentLongRT(self):
        self.percentLongRT = self.dfTest[self.dfTest['rt']>10000]['rt'].mean()
        
    def medianRT(self):
        self.medianRT = self.dfTest['rt'].median()

    def maxRT(self):
        self.maxRT = self.dfTest['rt'].max()
    
    def meanOverallAcc(self):
        self.meanOverallAcc = self.dfTest['hit'].mean()
    
    def per_block_learning_curve(self):
        if self.codeversion == "4.2" or self.codeversion == "4.3":
            blocks = ones(10)*stimuliperblock
        else:
            blocks = ones(15)*stimuliperblock
        for line in range(len(self.datafileFTest)):
            blocks[self.datafileFTest[line][5]-1] -= float(self.datafileFTest[line][12])
        self.learnCurve = 1.0-(blocks/stimuliperblock)

# <codecell>


