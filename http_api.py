from flask import Flask, request, abort
import time
import requests
import config as cfg
import utils.log as log
import logging
import json

def timestamp2str(ts):
    time_array = time.localtime(ts)
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return time_str

class HTTPApi():
    def __init__(self, pushworker) -> None:
        log.info(["API"],"Initiating.")
        self.pw = pushworker
        self.app = Flask("http_api")
        if cfg.get_value("LOG_LEVEL",0) !=0:
            flask_log = logging.getLogger('werkzeug')
            flask_log.disabled = True
        # GET API
        self.app.add_url_rule("/shutdown", view_func=self.shutdown, methods=['GET'])
        self.app.add_url_rule("/", view_func=self.index,  methods=['GET'])
        self.app.add_url_rule("/api/tasks", view_func=self.get_task_list, methods=['GET'])
        self.app.add_url_rule("/api/task/<name>", view_func=self.get_tast_detial, methods=['GET'])

        # POST API
        if cfg.get_value("API_ALLOW_WRITE", False):
            # self.app.add_url_rule("/api/tasks", view_func=self.post_task, methods=['POST'])
            self.app.add_url_rule("/api/task/<name>/running", view_func=self.post_task_running, methods=['POST'])
            self.app.add_url_rule("/api/task/<name>/clear", view_func=self.post_task_clear, methods=['POST'])
            self.app.add_url_rule("/api/reload", view_func=self.post_reload, methods=['POST'])


        @self.app.before_request
        def verify_check():
            if request.path == "/shutdown":
                if request.remote_addr == "127.0.0.1":
                    return
                else:
                    abort(401)
            else:
                verify_url = cfg.get_value("API_VERIFY_URL","")
                if verify_url:
                    return
                else:
                    return

    def run(self):
        log.info(["API"],"Starting.")
        self.app.run("0.0.0.0",cfg.get_value("API_PORT",8080),False)

    def index(self):
        """ / """
        return ""

    def get_task_list(self):
        """ [GET] /api/tasks """
        res_data_list = []
        for task_name in self.pw.task_data:
            res_data_list.append({
                "name":self.pw.task_data[task_name]["name"],
                "type":self.pw.task_data[task_name]["type"],
                "running":self.pw.task_data[task_name]["running"],
                "last_update":timestamp2str(self.pw.history[task_name]["time"]),
                "data":self.pw.history[task_name]["data"]
            })
        res_data = {
            "status":"ok",
            "msg":"成功",
            "data":res_data_list
        }
        return json.dumps(res_data)

    def get_tast_detial(self,name):
        """ [GET] /api/task/<name> """
        if name not in self.pw.task_data:
            res_data = {
                "status":"error",
                "msg":"没有对应的任务",
                "data":{}
            }
            return json.dumps(res_data)
        else:
            res_data_detail = {
                "name":self.pw.task_data[name]["name"],
                "type":self.pw.task_data[name]["type"],
                "running":self.pw.task_data[name]["running"],
                "last_update":timestamp2str(self.pw.history[name]["time"]),
                "data":self.pw.history[name]["data"],
                "raw":json.dumps(self.pw.task_data[name])
            }
            res_data = {
                "status":"ok",
                "msg":"成功",
                "data":res_data_detail
            }
            return json.dumps(res_data)

    def post_task(self):
        """ [POST] /api/tasks """
        req_text = request.data
        task_config = json.loads(req_text)
        if self.pw.task_verify(task_config):
            res = "ok"
        else:
            res = "error"
        return res

    def post_task_running(self,name):
        """ [POST] /api/task/<name>/running """
        if name not in self.pw.task_data:
            res_data = {
                "status":"error",
                "msg":"没有对应的任务",
                "data":{}
            }
            return json.dumps(res_data)
        else:
            req_text = request.data
            req_data = json.loads(req_text)
            tmp_running = req_data.get("running")
            if tmp_running == True:
                self.pw.start_task(name)
                tmp_status = "ok"
                tmp_msg = "任务已开始"
            elif tmp_running == False:
                self.pw.stop_task(name)
                tmp_status = "ok"
                tmp_msg = "任务已暂停"
            else:
                tmp_status = "error"
                tmp_msg = "请求数据错误"
                log.info(["API"],"Invalid request data.")

            res_data = {
                "status":tmp_status,
                "msg":tmp_msg,
                "data":{}
            }
            return json.dumps(res_data)

    def post_task_clear(self,name):
        """ [POST] /api/task/<name>/clear """
        if name not in self.pw.task_data:
            res_data = {
                "status":"error",
                "msg":"没有对应的任务",
                "data":{}
            }
            return json.dumps(res_data)
        else:
            self.pw.clear_history(name)
            res_data = {
                "status":"ok",
                "msg":"清理历史数据成功",
                "data":{}
            }
            return json.dumps(res_data)

    def post_reload(self):
        """ [POST] /api/reload """
        self.pw.reload()
        res_data = {
            "status":"ok",
            "msg":"重载成功",
            "data":{}
        }
        return json.dumps(res_data)

    def shutdown(self):
        log.info(["API"],"Shutting down.")
        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        if shutdown_func is None:
            raise RuntimeError('Not running werkzeug')
        shutdown_func()
        return "Shutting down..."

    

            
    
    

