import logging
import sys
import json
import os
import subprocess
import threading
import re
import shlex
from datetime import datetime


class BakeUp:

    def __init__(self, config_file):
        self.__init_logger()
        self.__load_config(config_file)

    def __init_logger(self):
        self.__logger = self.__get_logger("bakeup")

    def cook(self):
        if "before-all" in self.__config and self.__config["before-all"] is not None:
            self.__execute_before_all(self.__config["before-all"])
        i = 1
        for backup in self.__config["backups"]:
            self.__execute_backup(backup, i)
            i += 1
        if "after-all" in self.__config and self.__config["after-all"] is not None:
            self.__execute_after_all(self.__config["after-all"])

    def __execute_backup(self, backup, index):
        self.__logger.info("Executing backup #%d" % index)
        backup_env = self.__base_env.copy()
        if "environment" in backup:
            backup_env.update(backup["environment"])
        if "before" in backup and backup["before"] is not None:
            self.__execute_before(backup["before"], backup_env)
        dry_run = backup["dry-run"] if "dry-run" in backup else False
        excludes = backup["excludes"] if "excludes" in backup else []
        includes = backup["includes"] if "includes" in backup else []
        additional_args = backup["additional_arguments"] if "additional_arguments" in backup else []
        filters = backup["filters"] if "filters" in backup else []
        bwlimit = backup["bwlimit"] if "bwlimit" in backup else None
        backup_dir = backup["backup-dir"] if "backup-dir" in backup else None
        checksum = backup["checksum"] if "checksum" in backup else False
        self.__execute_rclone(dry_run, backup["source"], backup["dest"], excludes, includes, filters, bwlimit,
                              backup_dir, checksum, additional_args, backup_env)
        if "after" in backup and backup["after"] is not None:
            self.__execute_after(backup["after"], backup_env)
        self.__logger.info("Done executing backup #%d" % index)

    def __execute_before_all(self, script):
        self.__logger.info("Executing 'before-all' script")
        for command in script:
            self.__exec(command, True, self.__base_env)
        self.__logger.info("Done executing 'before-all' script")

    def __execute_after_all(self, script):
        self.__logger.info("Executing 'after-all' script")
        for command in script:
            self.__exec(command, True, self.__base_env)
        self.__logger.info("Done executing 'after-all' script")

    def __execute_before(self, script, env):
        self.__logger.info("Executing 'before' script")
        for command in script:
            self.__exec(command, True, env)
        self.__logger.info("Done executing 'before' script")

    def __execute_rclone(self, dry_run, source, dest, excludes, includes, filters, bwlimit, backup_dir, checksum, args,
                         env):
        self.__logger.info("Performing backup")
        command = ["rclone", "sync", "--links", "--metadata"]
        if dry_run is True:
            command.append("--dry-run")
        for exclude in excludes:
            command.extend(["--exclude", exclude])
        for include in includes:
            command.extend(["--include", include])
        for f in filters:
            command.extend(["--filter", f])
        for arg in args:
            command.append(arg)
        if bwlimit:
            command.extend(["--bwlimit", bwlimit])
        if backup_dir:
            command.extend(["--backup-dir", self.__replace_date(backup_dir)])
        if checksum is True:
            command.append("--checksum")
        command.extend([source, self.__replace_date(dest)])
        self.__exec(command, False, env)
        self.__logger.info("Backup done")

    def __execute_after(self, script, env):
        self.__logger.info("Executing 'after' script")
        for command in script:
            self.__exec(command, True, env)
        self.__logger.info("Done executing 'after' script")

    def __exec(self, args, shell, env):
        if len(args) < 1:
            return
        if type(args) is str:
            program_name = os.path.basename(shlex.split(args)[0])
        else:
            program_name = os.path.basename(args[0])
        logger = self.__get_logger(program_name)
        with subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, env=env) as process:
            stdout_thread = threading.Thread(target=self.__log_ouput, args=(process.stdout, logger.info))
            stderr_thread = threading.Thread(target=self.__log_ouput, args=(process.stderr, logger.warning))
            stdout_thread.start()
            stderr_thread.start()
            stdout_thread.join()
            stderr_thread.join()

    @staticmethod
    def __log_ouput(output_stream, logger):
        for line in output_stream:
            logger(line.rstrip())

    @staticmethod
    def __replace_date(s):
        match = re.search(r"{{date\?(.*?)}}", s)
        if match:
            return s.replace(match.group(0), datetime.now().strftime(match.group(1)))
        return s

    def __load_config(self, config_file_path):
        self.__logger.info("Loading configuration file...")
        with open(config_file_path, "r") as config_file:
            self.__config = json.load(config_file)
            self.__base_env = os.environ.copy()
            if "environment" in self.__config:
                self.__base_env.update(self.__config["environment"])
            self.__logger.info("Config loaded")

    @staticmethod
    def __get_logger(name):
        logger = logging.getLogger(name)
        if not logger.hasHandlers():
            logger.setLevel(logging.INFO)
            stdout_handler = logging.StreamHandler(sys.stdout)
            log_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            stdout_handler.setFormatter(log_format)
            logger.addHandler(stdout_handler)
        return logger
