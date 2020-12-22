'''''''''''
Module 사용
'''''''''''
import smbus # CDC 조도 센서
import RPi.GPIO as GPIO # 라즈베리파이의 GPIO 사용하며, 호출명을 GPIO로 지정
from multiprocessing import Process # 멀티프로세싱 모듈에서 Process
from mfrc522 import SimpleMFRC522 # mfrc522 모듈에서 SimpleMFRC522
from tkinter import * # Tkinter 모듈의 모든 함수
from time import * # Time 모듈에서 모든 함수
import pymysql
import threading
import cv2
import numpy as np
from os import listdir # os 모듈에서 listdir 함수를 선택
from os.path import isfile, join # os.path 모듈에서 isfile, Join 함수를 선택
import psutil

'''''''''''''''
글로벌 변수 선언 
'''''''''''''''
### 현재 시간을 now로 지정 ###
now = localtime()

### 조도 센서 ###
bus = smbus.SMBus(1)
bus.write_byte(0x48, 0)
last_reading = -1

### GPIO Setting###
GPIO.setmode(GPIO.BCM) # GPIO setting을 BCM mode로 설정

GPIO.setup(17, GPIO.IN) # 17번 핀을 입력으로 설정(수동 스위치)

GPIO.setup(5, GPIO.OUT) # 5번 핀을 출력으로 living_room_LED 설정
GPIO.setup(6, GPIO.OUT) # 6번 핀을 출력으로 bed_room_LED 설정 
GPIO.setup(18, GPIO.OUT) # 18번 핀을 출력으로 설정(서보 모터)
GPIO.setup(20, GPIO.OUT) # 20번 핀을 출력으로 kitchen_LED 설정
GPIO.setup(21, GPIO.OUT) # 21번 핀을 출력으로 bath_room_LED 설정
GPIO.setup(22, GPIO.OUT) # 22번 핀을 출력으로 Green LED 설정
GPIO.setup(23, GPIO.OUT) # 23번 핀을 출력으로 Red LED 설정

GPIO.setwarnings(False) # GPIO Setting 경고 메시지 무시

### RFID ###
reader = SimpleMFRC522()

### Press Number to * ###
input_pwd = "" # 도어락 숫자 버튼 입력값

### Light Sensor ###
count = 3
Fc_count = 4
Light_Check = 0

### Passwd Change ###
Passwd_Change = ""

##### Data Base Setting #####
db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
cursor = db.cursor()

sql = "SELECT * FROM doorlock"
cursor.execute(sql)
result = cursor.fetchall()
input_data = result[0][4] # 서버에 Door_Open 명령
output_data = result[0][5] # 문이 여닫힘 유무를 서버에 저장
passwd_data = result[0][6] # 서버에 저장된 패스워드
Temp_pwd = result[0][7] # 임시 비밀번호
inner = result[0][8] # 내부 출입인원
passwd_input = "" # 입력된 비밀번호
db.commit()
db.close()

#### Pi Camera ####
cap = cv2.VideoCapture(-1)

data_path = 'faces/'
onlyfiles = [f for f in listdir(data_path) if isfile(join(data_path,f))]

Training_Data, Labels = [], []

for i, files in enumerate(onlyfiles):
    image_path = data_path + onlyfiles[i]
    images = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    Training_Data.append(np.asarray(images, dtype=np.uint8))
    Labels.append(i)

Labels = np.asarray(Labels, dtype=np.int32)

model = cv2.face.LBPHFaceRecognizer_create()
model.train(np.asarray(Training_Data), np.asarray(Labels))

face_classifier = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

'''''''''
함수 선언
'''''''''
#### Pi Camera ####
def face_detector(img, size=0.5):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)

        if faces is ():
            return img, []

        for(x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 2)
            roi = img[y:y+h, x:x+w]
            roi = cv2.resize(roi, (200, 200))

        return img, roi
    except:
        cap.release()


### RFID ###
def RFID_Check():
    global output_data
    global inner    
    
    while(True):
        try:
            db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
            cursor = db.cursor()

            sql = "SELECT * FROM doorlock"
            cursor.execute(sql)
            result = cursor.fetchall()
            output_data = result[0][5] # 문이 여닫힘 유무를 서버에 저장
            inner = result[0][8] # 내부 출입인원
            db.commit()
            db.close()
        
            id, text = reader.read()
            
            if output_data == 0:
                if id == 869159747421:
                    Door_Open()
                    Auto_Lock()
                    Inner_Check()

                elif id == 806380005020:
                    Door_Open()
                    Auto_Lock()
                    Inner_Check()

                else:
                    print("등록되지 않은 정보입니다.")
                    sleep(1)
                
        except KeyboardInterrupt:
            break


# 빛 감지에 의한 자동 개폐
def Auto_Lock():
    global count
    global timer
    global Light_Check
    
    input_value = GPIO.input(17)
    Light_value = abs(bus.read_byte(0x48))
    timer = threading.Timer(1, Auto_Lock)
    timer.start()
    
    count -= 1

    if Light_value <= 200: # 빛 감지 상태
        count = 3
        Light_Check = 1
        
    elif Light_value >= 200: # 빛 미감지 상태
        if count == 0:
            timer.cancel()
            count = 3
            Door_Close()
            Light_Check = 0
    
    if input_value == True:
        timer.cancel()
        count = 3
        Door_Close()
        Light_Check = 0
        

### 내부 인원 체크 ###        
def Inner_Check():
    global inner
    
    db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
    cursor = db.cursor()
    sql = "SELECT * FROM doorlock"
    cursor.execute(sql)
    
    result = cursor.fetchall()
    inner = result[0][8]
    db.commit()
    db.close()
    
    inner += 1
                    
    db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
    cursor = db.cursor()
    sql = "UPDATE doorlock SET inner_person = {} WHERE dStatus = 'off'".format(inner)
    cursor.execute(sql)
    db.commit()
    db.close()


# 잠금장치 열림
def Door_Open():
    global output_data
    
    db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
    cursor = db.cursor()
    sql = "SELECT * FROM doorlock"
    cursor.execute(sql)
    
    result = cursor.fetchall()
    output_data = result[0][5]
    db.commit()
    db.close()
    
    if output_data == 0:
        print("Door Open")

        p = GPIO.PWM(18, 50)
        p.start(0)
        p.ChangeDutyCycle(2.5)
        GPIO.output(22, True)
        sleep(1)
        GPIO.output(22, False)
        p.stop()

        db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
        cursor = db.cursor()
        reset_sql = "UPDATE doorlock SET output = 1 WHERE dStatus = 'off'"
        cursor.execute(reset_sql)      
        db.commit()
        db.close()
        

# 잠금장치 잠김
def Door_Close():
    global output_data
    
    db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
    cursor = db.cursor()
    sql = "SELECT * FROM doorlock"
    cursor.execute(sql)
    
    result = cursor.fetchall()
    output_data = result[0][5]
    db.commit()
    db.close()
    
    if output_data == 1:
        print("Door Close")
        
        auto_ledON()
        
        p = GPIO.PWM(18, 50)
        p.start(0)
        p.ChangeDutyCycle(9)
        GPIO.output(23, True)
        sleep(1)
        GPIO.output(23, False)
        p.stop()
        
        db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
        cursor = db.cursor()
        reset_sql = "UPDATE doorlock SET output = 0 WHERE dStatus = 'off'"
        cursor.execute(reset_sql)  
        db.commit()
        db.close()
 
 
### 시간 설정으로 조명 자동제어 ###            
def auto_ledON():
    global inner

    db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
    cursor = db.cursor()
    device_sql = "SELECT * FROM devices"
    cursor.execute(device_sql)
    result = cursor.fetchall()
    led_status = result[0][2] # LED 상태
    db.commit()
    db.close()
    
    if inner >= 1: 
        if led_status == "off":
            print("Light ON")
            db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
            cursor = db.cursor()
            led_sql = "UPDATE devices SET dStatus = 'on'"
            cursor.execute(led_sql)
            db.commit()
            db.close()      

    elif inner == 0:
        if led_status == "on":
            print("Light OFF")
            db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
            cursor = db.cursor()
            led_sql = "UPDATE devices SET dStatus = 'off'"
            cursor.execute(led_sql)
            db.commit()
            db.close()
            
            
#### Tkinter User Interface ####
def Show_Dialog():         
    # Tkinter Watch
    def Update_ymd(): # 연/월/일 표기
        now = localtime()
        ymd = "%04d/%02d/%02d" %(now.tm_year, now.tm_mon, now.tm_mday)
        lblymd.configure(text=ymd)
        lblymd.after(1000, Update_ymd)
        
        
    def Update_hms(): # 시/분/초 표기
        now = localtime()
        hms = "%02d:%02d:%02d" %(now.tm_hour, now.tm_min, now.tm_sec)
        lblhms.configure(text=hms)
        lblhms.after(1000, Update_hms)
    
    
    # Tkinter Number Event      
    def press_1():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "1"

        
    def press_2():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "2"
        

    def press_3():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "3"


    def press_4():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "4"


    def press_5():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "5"


    def press_6():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "6"


    def press_7():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "7"
             

    def press_8():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "8"


    def press_9():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "9"


    def press_0():
        global passwd_input
        global input_pwd
        
        input_pwd += "*"
        lblstar['text'] = input_pwd
        passwd_input += "0"
        
    
    def Font_Change(): # 일정 시간 후 텍스트 변환
        global Fc_count
        
        timer = threading.Timer(1, Font_Change)
        timer.start()
            
        Fc_count -= 1

        if Fc_count == 0:
            lbl0['text'] = ""
            timer.cancel()
            Fc_count = 4
            
            
    def Font_Change2(): # 일정 시간 후 텍스트 변환
        global Fc_count
        
        timer = threading.Timer(1, Font_Change2)
        timer.start()
            
        Fc_count -= 1

        if Fc_count == 0:
            lblNp['text'] = ""
            timer.cancel()
            Fc_count = 4
        
        
    def press_Ok():
        global passwd_input
        global passwd_data
        global output_data
        global input_pwd
        global Temp_pwd
        global inner
        
        db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
        cursor = db.cursor()
        sql = "SELECT * FROM doorlock"
        cursor.execute(sql)
        result = cursor.fetchall()
        output_data = result[0][5] # 문이 여닫힘 유무를 서버에 저장
        passwd_data = result[0][6] # 서버에 저장된 패스워드
        Temp_pwd = result[0][7] # 임시 비밀번호
        inner = result[0][8] # 내부 출입인원
        db.commit()
        db.close()

        if output_data == 0:
            if Temp_pwd != "0":
                if passwd_input == Temp_pwd:
                    input_pwd = ""
                    passwd_input = ""
                    Temp_pwd = "0"

                    db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
                    cursor = db.cursor()
                    sql = "UPDATE doorlock SET temppwd = '0' WHERE dStatus = 'off'"
                    cursor.execute(sql)
                    db.commit()
                    db.close()

                    lblstar['text'] = input_pwd
                    lbl0['text'] = "< Success >"
                
                    Door_Open()
                    Font_Change()
                    Auto_Lock()
                    Inner_Check()

                elif passwd_input == passwd_data:
                    passwd_input = ""
                    input_pwd = ""
                    lblstar['text'] = input_pwd
                    lbl0['text'] = "< Success >"
                    
                    Door_Open()
                    Font_Change()
                    Auto_Lock()
                    Inner_Check()

                else:
                    passwd_input = ""
                    input_pwd = ""
                    lblstar['text'] = input_pwd
                    lbl0['text'] = "<   F a i l   >"
                    Font_Change()
                    
            elif passwd_input == passwd_data:
                passwd_input = ""
                input_pwd = ""
                lblstar['text'] = input_pwd
                lbl0['text'] = "< Success >"
                
                Door_Open()
                Font_Change()
                Auto_Lock()
                Inner_Check()

            else:
                passwd_input = ""
                input_pwd = ""
                lblstar['text'] = input_pwd
                lbl0['text'] = "<   F a i l   >"
                Font_Change()
                
        elif output_data == 1:
            print("문을 닫고 잠긴 다음 다시 시도하여 주십시오.")
        

    def press_Ht():
        global passwd_input
        global input_pwd

        if Light_Check == 1:
            if passwd_input == "":
                lblNp['text'] = "< 새 비밀번호 입력 후 #을 누르세요. >"
                
            elif passwd_input != "":
                Passwd_Change = passwd_input
                passwd_input = ""
                
                lblNp['text'] = "< 성공적으로 변경이 완료되었습니다. >"
                Font_Change2()
                lblstar['text'] = ""
                input_pwd = ""     
                   
                db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
                cursor = db.cursor()
                sql = "UPDATE doorlock SET passwd = {} WHERE dStatus = 'off'".format(Passwd_Change)
                cursor.execute(sql)
                db.commit()
                db.close()
                

    root = Tk()
    root.title("Home IoT DoorLock")
    root.geometry("800x480")
    root.resizable(False, False)
    
    now = localtime()
    ymd = "%04d/%02d/%02d" %(now.tm_year, now.tm_mon, now.tm_mday)
    hms = "%02d:%02d:%02d" %(now.tm_hour, now.tm_min, now.tm_sec)
    
    img1 = PhotoImage(file="icons/one.png")
    img2 = PhotoImage(file="icons/two.png")
    img3 = PhotoImage(file="icons/three.png")
    img4 = PhotoImage(file="icons/four.png")
    img5 = PhotoImage(file="icons/five.png")
    img6 = PhotoImage(file="icons/six.png")
    img7 = PhotoImage(file="icons/seven.png")
    img8 = PhotoImage(file="icons/eight.png")
    img9 = PhotoImage(file="icons/nine.png")
    img0 = PhotoImage(file="icons/zero.png")
    imgOk = PhotoImage(file="icons/ok.png")
    imgHt = PhotoImage(file="icons/hashtag.png")
    imgTdr = PhotoImage(file="icons/Light.png")
    
    Time_frame = Frame(root, bg = "black", padx = 50, pady = 2)
    Time_frame.place(x = 380, y = 5)
    Light_frame = Frame(root)
    Light_frame.place(x = 379, y = 245)
    Passwd_frame = Frame(root, bg = "black", padx = 41, pady = 46)
    Passwd_frame.place(x = 380, y = 112)
    
    btn1 = Button(root, image = img1, width = 120, height = 114, command = press_1)
    btn1.grid(row=0,column=0)
    btn2 = Button(root, image = img2, width = 120, height = 114, command = press_2)
    btn2.grid(row=0,column=1)
    btn3 = Button(root, image = img3, width = 120, height = 114, command = press_3)
    btn3.grid(row=0,column=2)
    btn4 = Button(root, image = img4, width = 120, height = 114, command = press_4)
    btn4.grid(row=1,column=0)
    btn5 = Button(root, image = img5, width = 120, height = 114, command = press_5)
    btn5.grid(row=1,column=1)
    btn6 = Button(root, image = img6, width = 120, height = 114, command = press_6)
    btn6.grid(row=1,column=2)
    btn7 = Button(root, image = img7, width = 120, height = 114, command = press_7)
    btn7.grid(row=2,column=0)
    btn8 = Button(root, image = img8, width = 120, height = 114, command = press_8)
    btn8.grid(row=2,column=1)
    btn9 = Button(root, image = img9, width = 120, height = 114, command = press_9)
    btn9.grid(row=2,column=2)
    btnOk = Button(root, image = imgOk, width = 120, height = 114, command = press_Ok)
    btnOk.grid(row=3,column=0)
    btn0 = Button(root, image = img0, width = 120, height = 114, command = press_0)
    btn0.grid(row = 3,column = 1)
    btnHt = Button(root, image=imgHt, width = 120, height = 114, command = press_Ht)
    btnHt.grid(row = 3,column = 2)

    lblymd = Label(Time_frame, text = ymd, font = ("궁서체", 30), bg = "black", fg = "white", padx = 45)
    lblymd.pack()
    lblhms = Label(Time_frame, text = hms, font = ("궁서체", 30), bg = "black", fg = "white")
    lblhms.pack()
    lblTdr = Label(Light_frame, image = imgTdr)
    lblTdr.pack()
    lbl0 = Label(Light_frame, text = "", font = ("궁서체", 30), bg = "black", fg = "white")
    lbl0.place(x = 85, y = 5)
    lblNp = Label(Passwd_frame, text = "", font = ("궁서체", 14), bg = "black", fg = "white")
    lblNp.place(x = 0, y = 45)
    lblname = Label(Light_frame, text = "Made by. 불켜조", font = ("궁서체", 15), bg = "black", fg = "white")
    lblname.place(x = 255, y = 200)
    lblpwd = Label(Passwd_frame, text = "Password : 　　　 　", font = ("궁서체", 25), bg = "black", fg = "white")
    lblpwd.pack()
    lblstar = Label(Passwd_frame, text = input_pwd, font = ("궁서체", 25), bg = "black", fg = "white")
    lblstar.place(x = 190, y = 8)
 
    Update_ymd()
    Update_hms()
    
    mainloop()
    

def Camera_Check():
    
    while(True):
        ret, frame = cap.read()
        
        image, face = face_detector(frame)

        try:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            result = model.predict(face)

            if result[1] < 500:
                confidence = int(100 * (1 - (result[1]) / 300))
                display_string = str(confidence)+'% Confidence it is user'

            if confidence > 85: # 일치율이 85%를 넘을 경우
                Door_Open()
                Auto_Lock()
                Inner_Check()
                confidence = 0
        
        except Exception as e:
            pass
            
            
### 실행 중인 프로세스 강제종료 ###
def Process_Kill():
    for proc in psutil.process_iter():
        try:
            # 프로세스 이름, PID값 가져오기
            processName = proc.name()
            processID = proc.pid

            if processName == "python3": # 프로세스명 = python3
                parent_pid = processID  # PID
                parent = psutil.Process(parent_pid) # PID 찾기
                for child in parent.children(recursive=True):  # 자식-부모 종료
                    child.kill()
                parent.kill()

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):   # 예외처리
            pass


'''''''''
__Main__
'''''''''           
# Multiprocessing
Process(target = RFID_Check).start()
Process(target = Show_Dialog).start()
Process(target = Camera_Check).start()

# DB 데이터 동기화
while(True):
    try:
        db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
        cursor = db.cursor()
        sql = "SELECT * FROM doorlock"
        cursor.execute(sql)
        
        result = cursor.fetchall()
        input_data = result[0][4]
        output_data = result[0][5]
        Temp_pwd = result[0][7]
        inner = result[0][8]
        db.commit()
        db.close()

        #### 수동 스위치 ####        
        input_value = GPIO.input(17)
        
        if input_data == 1:
            if output_data == 0:

                Door_Open()
                Auto_Lock()
                Inner_Check()
                
                db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
                cursor = db.cursor()
                reset_sql = "UPDATE doorlock SET input = 0 WHERE dStatus = 'off'"
                cursor.execute(reset_sql)
                db.commit()
                db.close()     

        elif input_data == 0:
            if output_data == 0:
                if input_value == True:
                    
                    Door_Open()
                    Auto_Lock()
                    
                    if inner >= 1:
                        inner -= 1
                            
                        db = pymysql.connect(host="192.168.0.185", port=3306, user="root", passwd="0000", db="project", charset='utf8')
                        cursor = db.cursor()
                        sql = "UPDATE doorlock SET inner_person = {} WHERE dStatus = 'off'".format(inner)
                        cursor.execute(sql)
                        db.commit()
                        db.close()
                        
            elif output_data == 1:        
                if input_value == True:
                    
                    Door_Close()
                 
    except KeyboardInterrupt:
        cap.release()
        GPIO.cleanup()
        Process_Kill()
        break