import json
import os.path
import time
import paho.mqtt.client as mqtt
import uuid
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from datetime import datetime
from log import Log_function


class funtion_class(QWidget):
    def __init__(self, ui=None):
        super().__init__()
        if ui is not None:
            self.mainUi = ui
            self.mainUi.btnInit.clicked.connect(self.btnInit_clicked)
            self.mainUi.btnUninit.clicked.connect(self.btnUninit_clicked)
            self.mainUi.btnSub.clicked.connect(self.btnSub_clicked)
            self.mainUi.btnPub.clicked.connect(self.btnPub_clicked)
            # 실제 통신 테스트----------------------------------------------
            self.mainUi.btnSubT.clicked.connect(self.btnSubT_clicked)
            # -----------------------------------------------------------
            self.log = Log_function()
            # region Log
            exe_path = os.path.abspath(".")
            log_folder = "Log"
            folder_path = os.path.join(exe_path, log_folder)
            self.log.make_directory(folder_path=folder_path)
            # endregion

            self.setup_UI()
            self.btnState(False)

            self.timer = QTimer(self)
            self.timer.setInterval(300)
            self.timer.timeout.connect(self.dataLabel_view)

    def setup_UI(self):
        self.mainUi.hostEdit.setText("220.76.90.180")
        self.mainUi.portEdit.setText("1884")
        # self.mainUi.userEdit.setText("hbrain")
        # self.mainUi.pwEdit.setText("0372")
        self.mainUi.topicEdit.setText("/front/#")
        # Subscribe Test Ui
        # call response
        self.mainUi.pub_call_response.setEnabled(False)
        self.mainUi.call_response_result.addItem("00: 정상")
        self.mainUi.call_response_result.addItem("10: 요청처리불가")

        # Publish
        # door open call
        self.mainUi.block_text.setText("1")
        self.mainUi.building_text.setText("204")
        self.mainUi.unit_text.setText("1102")

    def btnState(self, b):
        self.mainUi.btnInit.setEnabled(not b)
        self.mainUi.btnUninit.setEnabled(b)
        self.mainUi.btnSub.setEnabled(b)
        self.mainUi.btnSubT.setEnabled(b)
        self.mainUi.btnPub.setEnabled(b)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("connected OK")
        else:
            print("connected error")

    def on_disconnect(self, client, userdata, flags, rc=0):
        print(str(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("subscribe OK")

    def on_message(self, client, userdata, msg):
        self.subMsg_parsing(msg)

    def btnInit_clicked(self):
        host = self.mainUi.hostEdit.toPlainText()
        port = int(self.mainUi.portEdit.toPlainText())
        user = self.mainUi.userEdit.toPlainText()
        pswd = self.mainUi.pwEdit.text()

        global client
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_subscribe = self.on_subscribe
        client.on_message = self.on_message
        # client.username_pw_set(username=user, password=pswd)
        client.connect(host, port)
        client.loop_start()

        global systemStatus, doorStatus, doorNowStatus
        systemStatus = False
        doorStatus = False
        doorNowStatus = "close"
        self.btnState(True)
        self.timer.start()
        self.table_counter = 0

    def btnUninit_clicked(self):
        client.loop_stop()
        self.timer.stop()

        self.btnState(False)

    def btnSub_clicked(self):
        topic = self.mainUi.topicEdit.toPlainText()
        client.subscribe(topic, 1)

    def btnSubT_clicked(self):
        if self.mainUi.door_open_check.isChecked():
            print("----door_open_call----")
            id = str(uuid.uuid1())
            door_id = "door-1"
            block    = int(self.mainUi.block_text.toPlainText())
            building = int(self.mainUi.building_text.toPlainText())
            unit     = int(self.mainUi.unit_text.toPlainText())
            type     = 1
            if self.mainUi.call_check.isChecked():
                type = 0
            topic = "/front/" + door_id + "/door/open/call"
            # publish("topic", "message")
            client.publish(topic, json.dumps({"id": id,
                                              "block": block,
                                              "building": building,
                                              "unit": unit,
                                              "type": type
                                              }))

    def btnPub_clicked(self):
        if self.mainUi.pub_status.isChecked():
            self.pub_systemStatus()
        elif self.mainUi.pub_call_response.isChecked():
            self.pub_doorOpen_response()
        elif self.mainUi.pub_door_state.isChecked():
            self.pub_doorState()

    def pub_systemStatus(self):
        print("----system_status----")
        door_id = "door-1"
        topic = "/front/" + door_id + "/system/status"
        status_sub = False
        door_status_sub = False
        if self.mainUi.status_value.isChecked():
            status_sub = True
        if self.mainUi.door_status_value.isChecked():
            door_status_sub = True
        client.publish(topic, json.dumps({"enabled": status_sub,
                                          "frontdoors": [{
                                              "id": "door-1",
                                              "enabled": door_status_sub
                                          }]
                                          }))

    def pub_doorOpen_response(self, list):
        print("----open_response----")
        # list = [[door-id, robot-id], [id, block, building, floor, type]]
        door_id = list[0][0]
        robot_id = list[0][1]
        topic = "/front/" + door_id + "/robot/" + robot_id + "/door/call/response"
        result = 0
        if self.mainUi.call_response_result.currentIndex() == 0:
            result = 0
        elif self.mainUi.call_response_result.currentIndex() == 1:
            result = 10

        client.publish(topic, json.dumps({"id": list[1][0],
                                          "block": list[1][1],
                                          "building": list[1][2],
                                          "floor": list[1][3],
                                          "result": result}))

    def pub_doorState(self):
        print("----door_state----")
        door_id = "door-1"
        robot_id = "wmr001"
        topic = "/front/" + door_id + "/robot/" + robot_id + "/door/state"
        block    = int(self.mainUi.block_text.toPlainText())
        building = int(self.mainUi.building_text.toPlainText())
        floor = 1
        state = 1
        if self.mainUi.door_open.isChecked():
            state = 0
        elif self.mainUi.door_close.isChecked():
            state = 1

        client.publish(topic, json.dumps({"block": block,
                                          "building": building,
                                          "floor": floor,
                                          "state": state}))

    def subMsg_parsing(self, msg):
        topic_list = msg.topic.split('/')
        log_list = ["", "", "", ""]
        log_list[0] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_list[1] = "PUB"
        log_list[2] = msg.topic
        log_list[3] = msg.payload

        door_id = topic_list[2]
        if topic_list[3] == 'system':
            if topic_list[4] == 'status':
                self.sub_systemStatus(topic_list, msg)
        elif topic_list[3] == 'robot':
            if topic_list[5] == 'door':
                if topic_list[6] == 'call':
                    self.sub_doorOpen(topic_list, msg)
                    if len(topic_list) < 8:
                        log_list[1] = "SUB"
                elif topic_list[6] == 'state':
                    self.sub_doorState(topic_list, msg)
        self.log.log_save(log_list)
        self.table_view(log_list)

    def sub_systemStatus(self, topic_list, msg):
        print("Pub topic:   system Status")
        sub_msg = json.loads(str(msg.payload.decode("utf-8")))
        sub_status = sub_msg.get("enabled")
        door_info = sub_msg.get("frontdoors")
        sub_id = ""
        sub_enabled = False
        for list in door_info:
            sub_id = list.get("id")
            sub_enabled = list.get("enabled")
        print("Pub Message: status:" + str(sub_status) +
              "/door_id: " + str(sub_id) + " /elevator_enabled:" + str(sub_enabled))
        global systemStatus, doorStatus
        systemStatus = sub_status
        doorStatus = sub_enabled

    def sub_doorOpen(self, topic_list, msg):
        if len(topic_list) > 7:
            print("Pub topic: door open response")
            sub_msg = json.loads(str(msg.payload.decode("utf-8")))
            sub_id = sub_msg.get("id")
            sub_block = sub_msg.get("block")
            sub_building = sub_msg.get("building")
            sub_floor = sub_msg.get("floor")
            sub_result = sub_msg.get("result")
            print("Pub Message: id:", str(sub_id), " /",
                  str(sub_block), "단지 ", str(sub_building), "동 ", str(sub_floor), "층/result: ", str(sub_result))
        else:
            print("Sub topic: door open")
            sub_msg = json.loads(str(msg.payload.decode("utf-8")))
            sub_id = sub_msg.get("id")
            sub_block = sub_msg.get("block")
            sub_building = sub_msg.get("building")
            sub_floor = sub_msg.get("floor")
            sub_type = sub_msg.get("type")
            print("Sub Message: id:", str(sub_id), " /",
                  str(sub_block), "단지 ", str(sub_building), "동 ", str(sub_floor), "층/type: ", str(sub_type))
            temp = [[topic_list[2], topic_list[4]], [sub_id, sub_block, sub_building, sub_floor, sub_type]]
            self.pub_doorOpen_response(temp)

    def sub_doorState(self, topic_list, msg):
        print("Pub topic: door state")
        sub_msg = json.loads(str(msg.payload.decode("utf-8")))
        sub_block = sub_msg.get("block")
        sub_building = sub_msg.get("building")
        sub_floor = sub_msg.get("floor")
        sub_state = sub_msg.get("state")
        print("Pub Message: ", str(sub_block), "단지 ", str(sub_building), "동 ", str(sub_floor), "층/state: ", str(sub_state))
        global doorNowStatus
        if sub_state == 0:
            doorNowStatus = "open"
        elif sub_state == 1:
            doorNowStatus = "close"

    def table_view(self, msg_list):
        self.mainUi.dataList_door.setRowCount(self.mainUi.dataList_door.rowCount() + 1)
        for i in range(4):
            if i == 0:
                self.table_item = str(msg_list[0])
            elif i == 1:
                self.table_item = str(msg_list[1])
            elif i == 2:
                self.table_item = str(msg_list[2])
            elif i == 3:
                self.table_item = str(msg_list[3])
            self.mainUi.dataList_door.setItem(self.table_counter, i, QTableWidgetItem(self.table_item))
        self.table_counter += 1
        self.mainUi.dataList_door.scrollToBottom()
        self.mainUi.dataList_door.resizeColumnsToContents()

    def dataLabel_view(self):
        global systemStatus, doorStatus, doorNowStatus
        self.mainUi.Status_label.setText(str(systemStatus))
        self.mainUi.doorStatus_label.setText(str(doorStatus))
        self.mainUi.door_state.setText(doorNowStatus)


