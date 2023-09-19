import paho.mqtt.client as mqtt
import json
import serial
import pymysql
import cv2
import numpy as np
from socket import *
from select import *
from time import sleep
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

HOST = "192.168.0.120"
PORT = 2004
BUFSIZE = 1024
ADDR = (HOST, PORT)


def dice_recognition():
    cap = cv2.VideoCapture(0)
    readings = [-1, -1]
    display = [0, 0]

    Circle_Inertia = 0.6
    Gaussian_ksize = (7, 7)
    canny_threshold_min = 100
    canny_threshold_max = 250

    params = cv2.SimpleBlobDetector_Params()
    params.filterByInertia = True
    params.minInertiaRatio = Circle_Inertia

    detector = cv2.SimpleBlobDetector_create(params)

    while True:
        ret, frame = cap.read()
        frame_blurred = cv2.GaussianBlur(frame, Gaussian_ksize, 1)
        frame_gray = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2GRAY)
        frame_canny = cv2.Canny(
            frame_gray,
            canny_threshold_min,
            canny_threshold_max,
            apertureSize=3,
            L2gradient=True,
        )

        keypoints = detector.detect(frame_canny)
        num = len(keypoints)
        readings.append(num)
        if (
            readings[-1]
            == readings[-2]
            == readings[-3]
            == readings[-4]
            == readings[-5]
            == readings[-6]
        ):
            im_with_keypoints = cv2.drawKeypoints(
                frame,
                keypoints,
                np.array([]),
                (0, 0, 255),
                cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
            )
            cv2.putText(
                im_with_keypoints,
                str(num),
                (500, 250),
                cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                5,
                (0, 255, 0),
            )
            socketTxData = bytes(
                [
                    76,
                    83,
                    73,
                    83,
                    45,
                    88,
                    71,
                    84,
                    0,
                    0,
                    0,
                    0,
                    160,
                    51,
                    0,
                    0,
                    22,
                    0,
                    0,
                    0,
                    88,
                    0,
                    2,
                    0,
                    0,
                    0,
                    1,
                    0,
                    8,
                    0,
                    37,
                    68,
                    87,
                    48,
                    49,
                    49,
                    48,
                    48,
                    2,
                    0,
                ]
            )
            num_little = num.to_bytes(2, "little")

            if num != 0:
                try:
                    clientSocket = socket(AF_INET, SOCK_STREAM)
                    clientSocket.connect(ADDR)
                    clientSocket.send(socketTxData + num_little)
                    clientSocket.close()
                except Exception as e:
                    print("Error" + str(e))
            return num


load_dotenv()

db = pymysql.connect(
    host="host.docker.internal",
    port=3333,
    user="abcd",
    passwd="1234",
    db="plc",
    charset="utf8",
)


PORT = "COM8"
BaudRate = 9600
ARD = serial.Serial(PORT, BaudRate)


def Decode(A):
    return int(A[0:3])


def Ardread():
    if ARD.readable():
        code = Decode(ARD.readline())
        return code
    else:
        print("읽기 실패")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK")
        client.on_subscribe = on_subscribe
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
    return rc


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


message = {"tagId": "12", "value": "1"}
dice = 0

mflag = True
dflag = True
trackflag = True
twoflag = False


def on_message1(client, userdata, msg):
    today = datetime.today().strftime("%Y-%m-%d")
    global mflag
    global message
    global dice
    global radiation
    global dflag
    global trackflag
    global twoflag
    radiation = 0
    data = msg.payload.decode("utf-8")
    data_dict = json.loads(msg.payload)
    cursor = db.cursor()
    sql = """INSERT INTO operation (date,first,second,third)
                SELECT current_date(),0,0,0
                from dual
                WHERE NOT EXISTS ( SELECT * FROM operation WHERE date = (%s))"""
    cursor.execute(sql, today)
    sql = """INSERT INTO misconduct (date,normal,defect)
    SELECT current_date(),0,0
    from dual
    WHERE NOT EXISTS ( SELECT * FROM misconduct WHERE date = (%s))"""
    cursor.execute(sql, today)
    TrackId = None
    if data_dict["Wrapper"][2]["value"] and trackflag:
        trackflag = False
        sql = """UPDATE operation SET first = first + 1 WHERE date = (%s)"""
        cursor.execute(sql, today)
        db.commit()
    elif data_dict["Wrapper"][2]["value"] == False:
        trackflag = True
    sql = "SELECT * FROM track order by id desc limit 1"
    cursor.execute(sql)
    row = cursor.fetchone()
    if not twoflag and data_dict["Wrapper"][3]["value"]:
        twoflag = True
    if twoflag and not data_dict["Wrapper"][3]["value"]:
        sql = """UPDATE operation SET second = second + 1 WHERE date = (%s)"""
        cursor.execute(sql, today)
        twoflag = False
    row = cursor.fetchone()

    sql = """INSERT INTO operation (date,first,second,third)
                    SELECT current_date(),0,0,0
                    from dual
                    WHERE NOT EXISTS ( SELECT * FROM operation WHERE date = (%s))"""
    cursor.execute(sql, today)
    trackid = None
    sql = "Select * from track order by id desc limit 1"
    data = msg.payload.decode("utf-8")
    cursor.execute(sql)
    r = cursor.fetchone()
    if r:
        trackid = r[0]
    data_dict = json.loads(msg.payload)
    dice = dice_recognition()
    sql = """SELECT * FROM misconduct where date = (%s)"""
    cursor.execute(sql, today)
    row = cursor.fetchone()
    if dice == 0:
        dflag = False
    if dice > 0 and dice < 7 and not dflag:
        dflag = True
        radiation = Ardread()
        stamp = datetime.strptime(
            data_dict["Wrapper"][40]["value"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        sql = """INSERT INTO dice (num,TrackId) VALUES (%s,%s)"""
        sqlradi = (
            """INSERT INTO radiation (figure,created_at,TrackId) VALUES (%s,%s,%s)"""
        )
        cursor.execute(sql, (dice, trackid))
        cursor.execute(sqlradi, (radiation, stamp, trackid))
    if dice >= 2 and dice <= 5 and radiation < 65:
        message = {"tagId": "11", "value": "1"}
        sql = """UPDATE operation SET third = third + 1 WHERE date = (%s)"""
        cursor.execute(sql, today)
        sql = """UPDATE misconduct set normal = (%s) where date = (%s)"""
        cursor.execute(sql, (int(row[1]) + 1, row[0]))
        mflag = False
    elif dice == 1 or dice == 6 or radiation >= 65:
        message = {"tagId": "11", "value": "0"}
        sql = """UPDATE misconduct set defect = (%s) where date = (%s)"""
        cursor.execute(sql, (int(row[2]) + 1, row[0]))
        mflag = False
    if mflag == False:
        client.publish("edukit/control", json.dumps(message), qos=1)
        mflag = True
    db.commit()


def on_message2(client, userdata, msg):
    data = msg.payload.decode("utf-8")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message1
client.connect("localhost", 1883)
client.subscribe("edukit/robotarm", 1)
client.on_disconnect = on_disconnect
client.loop_forever()
