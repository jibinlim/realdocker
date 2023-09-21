import logging
import pymysql
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import threading
import os
from dotenv import load_dotenv

lock = threading.Lock()
load_dotenv()


app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
logging.getLogger("flask_cors").level = logging.DEBUG

db = pymysql.connect(
    host="svc.sel5.cloudtype.app",
    port=30039,
    user="root",
    passwd="1234",
    db="plc",
    charset="utf8",
)


@app.route("/")
def home():
    return "Hello World"


@app.route("/dice")
def index():
    start = request.args.get("start")
    end = request.args.get("end")
    cursor = db.cursor()
    sql = """SELECT * FROM dice where created_at between (%s) and (%s)"""
    cursor.execute(sql, (start, end))
    result = cursor.fetchall()
    data = [
        {
            "id": row[0],
            "num": row[1],
            "created_at": datetime.strftime(row[2], "%Y/%m/%d %H:%M:%S"),
        }
        for row in result
    ]
    return jsonify(data)


@app.route("/track")
def track():
    id = request.args.get("id")
    cursor = db.cursor()
    sql = """SELECT * FROM track where id = (%s)"""
    cursor.execute(sql, id)
    result = cursor.fetchone()
    data = [
        {
            "id": result[0],
            "start": datetime.strftime(result[1], "%Y/%m/%d %H:%M:%S"),
            "end": datetime.strftime(result[1], "%Y/%m/%d %H:%M:%S"),
        }
    ]

    return jsonify(data)


@app.route("/log")
def log():
    trackid = request.args.get("track")
    cursor = db.cursor()
    sql = """SELECT * FROM record where TrackId = (%s)"""
    cursor.execute(sql, (trackid))
    row = cursor.fetchall()
    data = [
        {
            "id": result[0],
            "Datetime": datetime.strftime(result[1], "%Y/%m/%d %H:%M:%S"),
            "Start": result[2],
            "No1Action": result[3],
            "No2InPoint": result[4],
            "No3Motor1": result[5],
            "No3Motor2": result[6],
            "Dicevalue": result[7],
        }
        for result in row
    ]

    return jsonify(data)


@app.route("/radiation")
def radiation():
    cursor = db.cursor()
    sql = """SELECT * from radiation"""
    cursor.execute(sql)
    result = cursor.fetchall()
    data = [
        {
            "id": row[0],
            "figure": row[1],
            "created_at": datetime.strftime(row[2], "%Y/%m/%d %H:%M:%S"),
        }
        for row in result
    ]

    return jsonify(data)


@app.route("/page")
def page():
    with lock:
        cursor = db.cursor()
        sql = """select count(*) from record"""
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        data = {"count": f"{count}", "results": [], "next": None}
        num = request.args.get("num")
        sql = """select * from record where id <= (select count(*) from record) - (50 * (%s)) order by id desc limit 50"""
        cursor.execute(sql, num)
        row = cursor.fetchall()
        for i in range(len(row)):
            data["results"].append(
                {
                    "id": row[i][0],
                    "Datetime": datetime.strftime(row[i][1], "%Y/%m/%d %H:%M:%S"),
                    "TrackId": row[i][8],
                    "Start": row[i][2],
                    "No1Action": row[i][3],
                    "No2InPoint": row[i][4],
                    "No3Motor1": row[i][5],
                    "No3Motor2": row[i][6],
                    "Dicevalue": row[i][7],
                }
            )
        if (int(num) + 1) * 50 < count:
            data["next"] = f"http://127.0.0.1:5002/page?num={int(num) + 1}"
        return jsonify(data)


@app.route("/tracklog")
def tracklog():
    with lock:
        track_id = request.args.get("track_id", type=int)
        data = {"results": [], "dice": None, "radiation": None}
        if not track_id:
            return jsonify(data)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM record WHERE TrackId = %s", (track_id))
        row = cursor.fetchall()
        for i in range(len(row)):
            data["results"].append(
                {
                    "id": row[i][0],
                    "Datetime": datetime.strftime(row[i][1], "%Y/%m/%d %H:%M:%S"),
                    "TrackId": row[i][8],
                    "Start": row[i][2],
                    "No1Action": row[i][3],
                    "No2InPoint": row[i][4],
                    "No3Motor1": row[i][5],
                    "No3Motor2": row[i][6],
                    "Dicevalue": row[i][7],
                }
            )
        sql = "SELECT * FROM dice WHERE TrackId = %s"
        cursor.execute(sql, track_id)
        row = cursor.fetchone()
        if row:
            if int(row[1]) == 1:
                data["dice"] = "규격미달"
            elif int(row[1]) == 6:
                data["dice"] = "규격초과"
            else:
                data["dice"] = "정상"
        sql = "SELECT * FROM radiation WHERE TrackId = %s"
        cursor.execute(sql, track_id)
        row = cursor.fetchone()
        if row:
            data["radiation"] = row[1]
        return jsonify(data)


@app.route("/misconduct")
def misconduct():
    with lock:
        start = request.args.get("start")
        end = request.args.get("end")
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM misconduct WHERE date >= %s and date <= %s order by date",
            (start, end),
        )
        row = cursor.fetchall()
        data = {"results": []}
        for i in range(len(row)):
            data["results"].append(
                {
                    "Datetime": datetime.strftime(row[i][0], "%Y/%m/%d"),
                    "normal": row[i][1],
                    "defect": row[i][2],
                }
            )
        return jsonify(data)


@app.route("/malfunction")
def malfuntion():
    with lock:
        start = request.args.get("start")
        end = request.args.get("end")
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM malfunction WHERE date >= %s and date <= %s order by date",
            (start, end),
        )
        row = cursor.fetchall()
        data = {"results": []}
        for i in range(len(row)):
            data["results"].append(
                {
                    "Datetime": datetime.strftime(row[i][0], "%Y/%m/%d"),
                    "normal": row[i][1],
                    "defect": row[i][2],
                }
            )
        return jsonify(data)


@app.route("/hastrack")
def malfunction():
    with lock:
        start = request.args.get("start")
        end = request.args.get("end")
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM hastrack WHERE date >= %s and date <= %s order by date",
            (start, end),
        )
        row = cursor.fetchall()
        data = {"results": []}
        for i in range(len(row)):
            data["results"].append(
                {
                    "Datetime": datetime.strftime(row[i][0], "%Y/%m/%d"),
                    "normal": row[i][1],
                    "defect": row[i][2],
                }
            )
        return jsonify(data)


@app.route("/gaslog")
def gaslog():
    with lock:
        start = request.args.get("start")
        end = request.args.get("end")
        end_obj = datetime.strptime(end, "%Y-%m-%d")
        new_date_obj = end_obj + timedelta(days=1)
        new_end = new_date_obj.strftime("%Y-%m-%d")
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM radiation WHERE created_at >= %s and created_at <= %s",
            (start, new_end),
        )

        row = cursor.fetchall()
        data = {"results": []}
        for i in range(len(row)):
            data["results"].append(
                {
                    "Datetime": datetime.strftime(row[i][2], "%Y/%m/%d %H:%M:%S"),
                    "radiation": row[i][1],
                    "TrackId": row[i][3],
                }
            )
        return jsonify(data)


@app.route("/dicelog")
def dicelog():
    with lock:
        start = request.args.get("start")
        end = request.args.get("end")
        end_obj = datetime.strptime(end, "%Y-%m-%d")
        new_date_obj = end_obj + timedelta(days=1)
        new_end = new_date_obj.strftime("%Y-%m-%d")
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM dice WHERE created_at >= %s and created_at <= %s",
            (start, new_end),
        )

        row = cursor.fetchall()
        data = {"results": []}
        for i in range(len(row)):
            data["results"].append(
                {
                    "Datetime": datetime.strftime(row[i][2], "%Y/%m/%d %H:%M:%S"),
                    "dice": row[i][1],
                    "TrackId": row[i][3],
                }
            )
        return jsonify(data)


@app.route("/operation")
def operation():
    with lock:
        start = request.args.get("start")
        end = request.args.get("end")
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM operation WHERE date >= %s and date <= %s order by date",
            (start, end),
        )
        row = cursor.fetchall()
        data = {"results": []}
        for i in range(len(row)):
            data["results"].append(
                {
                    "Datetime": datetime.strftime(row[i][0], "%Y/%m/%d"),
                    "first": row[i][1],
                    "second": row[i][2],
                    "third": row[i][3],
                }
            )
        return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
