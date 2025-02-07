import subprocess
from pathlib import Path

import pymongo
import yaml


class MongoDB:
    def __init__(self, conf_file: str = "mongod.conf") -> None:
        self.conf_file = conf_file
        self.conf_data = None
        self._client = None

    def load_conf(self, conf_data=None):
        if not conf_data:
            with open(self.conf_file, "r") as file:
                conf_data = yaml.safe_load(file)
        self.host = conf_data["net"]["bindIp"]
        self.port = conf_data["net"]["port"]
        return conf_data

    def write_conf(self, conf_data):
        with open(self.conf_file, "w") as yaml_file:
            yaml.dump(conf_data, yaml_file)

    def run_daemon(self) -> None:
        conf_data = self.load_conf()
        dbpath = Path(conf_data["storage"]["dbPath"])
        dbpath.mkdir(parents=True, exist_ok=True)
        log_path = dbpath.joinpath("logs")
        log_path.mkdir(exist_ok=True)
        log_path.joinpath("mongod.log").touch()

        conf_data["systemLog"]["path"] = log_path.joinpath("mongod.log").as_posix()
        self.write_conf(conf_data)
        self.load_conf(conf_data)

        try:
            subprocess.run(["mongod", "--config", self.conf_file], check=True)
        except subprocess.CalledProcessError:
            print("[ERROR] Shutting down MongoDB server ....")

    def connect(self):
        if not self._client:
            self._client = pymongo.MongoClient(host=self.host, port=self.port)
        return self._client

    @property
    def client(self):
        return self.connect()

    def disconnect(self) -> None:
        self.connect().admin.command("shutdown")
