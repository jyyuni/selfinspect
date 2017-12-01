#-*- coding:utf-8 -*-

# ======================================================================= 
# =======================================================================  


import logging
from flask import Flask,request,jsonify
import requests
import time
#日志输出定义  
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='selfInspectLog.log',
                filemode='w')
#定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console) 
           
# 输出日志级别      
logging.info('logger info message')   
logging.error('logger error message') 
logging.debug('logger debug message')   

#服务接口
app = Flask(__name__)

#定义前端请求接口,获取注册需要的数据
@app.route('%s%s'%(route,'/selfinspect'),methods=['POST'])
def dataQuery():
    logging.info('dataQuery begin',request.form)
    
    testType=request.args.get('testType')
    appId=request.args.get('appId')
    userId=request.args.get('userId')
    startTime=request.args.get('startTime')
    endTime=request.args.get('endTime')
    #历史记录查询
    if(testType=='hisRegister'):
        hisQue={'appId':appId,'userId':userId,'testType':testType,'startTime':startTime,'endTime':endTime}
        r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/查询注册结果接口'), data=jsonify(hisQue))
        logging.info('Query data',r)
    
    if(testType=='hisVerify'):
        hisQue={'appId':appId,'userId':userId,'testType':testType,'startTime':startTime,'endTime':endTime}
        r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/查询验证结果接口'), data=jsonify(hisQue))
        logging.info('Query data',r)
    
    #巡检
    if(testType=='register' or testType=='verify'):    
        queReq={'testType':testType,'appId':appId}
        r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/获取数据接口'), data=jsonify(queReq))
        logging.info('Query data',r)
    
    response={'responseCode':'200','responseMessage':'request accpeted'}
    return jsonify(response)

#接收获取的数据,注册，并查询注册结果
@app.route('%s%s'%(route,'/register'),methods=['POST'])
def register():
    logging.info('register begin',request.args)
    
    userId=request.args.get('userId')
    appId=request.args.get('appId')
    regCallId=request.args.get('regCallId')
    valiCallId=request.args.get('valiCallId')
    regSerial=request.args.get('regSerial')
    valiSerial=request.args.get('valiSerial')
    #本次注册请求是注册巡检或者验证巡检
    testType=request.args.get('testType')
    
    #consumerId=TEST+userid+时间戳
    now=time.time
    consumerId='%s%s%s'%('TEST',userId,int(now))
     
    #信用卡注册请求组装及注册
    if(appId=='10008'):
        scene='p2p_cll'
        req='register'
        regReq={'consumerId':consumerId,'appId':appId,'scene':scene,'type':req,'callId':regCallId}
    
        #注册    
        r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/credit/trasferCommand'), data=jsonify(regReq))
        logging.info('register begin',jsonify(regReq))
        logging.info('register request',r)
    
    #等待10min后查询结果
    time.sleep(600)
    
    #查询注册结果
    regQue={'userId':consumerId,'appId':appId,'regCallId':regCallId,'valiCallId':valiCallId,'regSerial':regSerial,'valiSerial':valiSerial,'testType':testType}
    
    r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/查询注册结果接口'), data=jsonify(regQue))
    logging.info('Query register result',r)
    
    response={'responseCode':'200','responseMessage':'request accpeted'}
    return jsonify(response)

#接收注册结果，注册巡检&&注册成功，返回结果到前端，否则查询原始数据；验证巡检&&注册失败，返回结果至前端，否则查询验证数据并开始验证
@app.route('%s%s'%(route,'/registerQuery'),methods=['POST'])
def registerQuery():
    logging.info('register result',request.args)
    
    userId=request.args.get('userId')
    appId=request.args.get('appId')
    regCallId=request.args.get('regCallId')
    valiCallId=request.args.get('valiCallId')
    regSerial=request.args.get('regSerial')
    valiSerial=request.args.get('valiSerial')
    testType=request.args.get('testType')
    userStatus=request.args.get('userStatus')
    
    if(testType.equals=='register'):
        #如果注册成功，结果为正常
        if(userStatus=='0000'):
            regNotify={'appId':appId,'userId':userId,'testType':testType,'result':'success','status':'normal'}
            r = requests.post(notify_url, data=jsonify(regNotify))
            logging.info('return register result',r)
        else:
            #如果注册失败，与原始数据进行对比
            origQue={'userId':userId,'appId':appId,'regCallId':regCallId,'valiCallId':valiCallId,'regSerial':regSerial,'valiSerial':valiSerial,'testType':testType}
            r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/查询原始数据接口'),data=jsonify(origQue))
            logging.info('Query original data',r)
            
    if(testType=='verify'):
        #如果注册成功，获取验证所要用的数据
        if(userStatus=='0000'):
            #信用卡验证请求组装并验证,并调用查询验证结果结果
            if(appId=='10008'):
                scene='p2p_cll'
                req='validation'
                regReq={'consumerId':userId,'appId':appId,'scene':scene,'type':req,'callId':valiCallId}
    
                #验证    
                r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/credit/trasferCommand'), data=jsonify(regReq))
                logging.info('verify begin',jsonify(regReq))
                logging.info('verify request',r)
            
            #等待200s后查询结果
            time.sleep(200)
    
            #查询验证结果
            veriQue={'userId':userId,'appId':appId,'regCallId':regCallId,'valiCallId':valiCallId,'regSerial':regSerial,'valiSerial':valiSerial,'testType':testType}
            r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/查询验证结果接口'), data=jsonify(veriQue))
            logging.info('Query verify result',r)
        else:
            #如果注册失败，返回结果至前端，异常
            regNotify={'appId':appId,'userId':userId,'testType':testType,'result':'register fail','status':'abnormal'}
            r = requests.post(notify_url, data=jsonify(regNotify))
            logging.info('return verify result',r)
            
    if(testType=='hisRegister'):
        regNotify={'appId':appId,'userId':userId,'testType':testType,'result':userStatus}
        r = requests.post(notify_url, data=jsonify(regNotify))
        logging.info('return history register result',r) 
                
    response={'responseCode':'200','responseMessage':'request accpeted'}
    return jsonify(response)

#获取查询原始数据记录的数据，比对判断是否异常之后，返回结果至前端
@app.route('%s%s'%(route,'/notify'),methods=['POST'])
def notify():
    logging.info('result notify',request.args)
    
    userId=request.args.get('userId')
    appId=request.args.get('appId')
    regCallId=request.args.get('regCallId')
    valiCallId=request.args.get('valiCallId')
    regSerial=request.args.get('regSerial')
    valiSerial=request.args.get('valiSerial')
    testType=request.args.get('testType')
    userStatus=request.args.get('userStatus')
    compResult=request.args.get('compResult')
    
    if(testType=='register'):
        #如果注册成功，本次注册结果与原始数据不同，不正常
        if(userStatus=='0000'):
            regNotify={'appId':appId,'userId':userId,'testType':testType,'result':'fail','status':'abnormal'}
            r = requests.post(notify_url, data=jsonify(regNotify))
            logging.info('return register result',r)
        else:
            #如果注册失败，本次注册结果与原始数据相同，正常
            regNotify={'appId':appId,'userId':userId,'testType':testType,'result':'fail','status':'normal'}
            r = requests.post(notify_url, data=jsonify(regNotify))
            logging.info('return register result',r)
            
    if(testType=='verify'):
        #如果验证成功，本次验证结果与原始数据不同，不正常
        if(userStatus=='0000' and compResult=='0'):
            regNotify={'appId':appId,'userId':userId,'testType':testType,'result':'fail','status':'abnormal'}
            r = requests.post(notify_url, data=jsonify(regNotify))
            logging.info('return verify result',r)
        else:
            #如果验证失败，本次验证结果与原始数据相同，正常
            regNotify={'appId':appId,'userId':userId,'testType':testType,'result':'fail','status':'normal'}
            r = requests.post(notify_url, data=jsonify(regNotify))
            logging.info('return verify result',r)
        
    response={'responseCode':'200','responseMessage':'request accpeted'}
    return jsonify(response)        

#接收验证结果，验证成功，返回结果到前端，否则查询原始数据;接收历史验证数据，返回给前端
@app.route('%s%s'%(route,'/verifyQuery'),methods=['POST'])
def verifyQuery():
    logging.info('verify result',request.args)
    
    userId=request.args.get('userId')
    appId=request.args.get('appId')
    regCallId=request.args.get('regCallId')
    valiCallId=request.args.get('valiCallId')
    regSerial=request.args.get('regSerial')
    valiSerial=request.args.get('valiSerial')
    testType=request.args.get('testType')
    userStatus=request.args.get('userStatus')
    compResult=request.args.get('compResult')
    
    if(testType=='verify'):
        #如果验证成功，结果为正常
        if(userStatus=='0000' and compResult=='0'):
            veriNotify={'appId':appId,'userId':userId,'testType':testType,'result':'success','status':'normal'}
            r = requests.post(notify_url, data=jsonify(veriNotify))
            logging.info('return verify result',r)
        else:
            #如果验证失败，与原始数据进行对比
            origQue={'userId':userId,'appId':appId,'regCallId':regCallId,'valiCallId':valiCallId,'regSerial':regSerial,'valiSerial':valiSerial,'testType':testType}
            r = requests.post('%s%s'%(vprc_url,'/vprc_core/rest/api/查询原始验证数据接口'),data=jsonify(origQue))
            logging.info('Query original data',r)
            
    if(testType=='hisVerify'):
        veriNotify={'appId':appId,'userId':userId,'testType':testType,'result':compResult,'status':userStatus}
        r = requests.post(notify_url, data=jsonify(veriNotify))
        logging.info('return history verify result',r)   
        
    response={'responseCode':'200','responseMessage':'request accpeted'}
    return jsonify(response)
    
if (__name__=='__main__'):
    app.run(host=activeHost,port=activePort,processes=1)
