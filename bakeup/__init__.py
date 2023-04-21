import logging
import sys
import json
import os
import subprocess
import threading


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
        if "before" in backup and backup["before"] is not None:
            self.__execute_before(backup["before"])
        dry_run = "dry-run" in backup and backup["dry-run"] is True
        exceptions = backup["exceptions"] if "exceptions" in backup else None
        self.__execute_rclone(dry_run, backup["source"], backup["dest"], exceptions)
        if "after" in backup and backup["after"] is not None:
            self.__execute_after(backup["after"])
        self.__logger.info("Done executing backup #%d" % index)

    def __execute_before_all(self, script):
        self.__logger.info("Executing 'before-all' script")
        for command in script:
            self.__exec(command, True)
        self.__logger.info("Done executing 'before-all' script")

    def __execute_after_all(self, script):
        self.__logger.info("Executing 'after-all' script")
        for command in script:
            self.__exec(command, True)
        self.__logger.info("Done executing 'after-all' script")

    def __execute_before(self, script):
        self.__logger.info("Executing 'before' script")
        for command in script:
            self.__exec(command, True)
        self.__logger.info("Done executing 'before' script")

    def __execute_rclone(self, dry_run, source, dest, exceptions):
        self.__logger.info("Performing backup")
        command = ["rclone", "sync", "--links", "--track-renames", "--delete-during"]
        if dry_run:
            command.append("--dry-run")
        if exceptions:
            for exception in exceptions:
                command.extend(["--exclude", exception])
        command.extend([source, dest])
        self.__exec(command, False)
        self.__logger.info("Backup done")

    def __execute_after(self, script):
        self.__logger.info("Executing 'after' script")
        for command in script:
            self.__exec(command, True)
        self.__logger.info("Done executing 'after' script")

    def __exec(self, args, shell):
        if len(args) < 1:
            return
        program_name = os.path.basename(args[0])
        logger = self.__get_logger(program_name)
        with subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True) as process:
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

    def __load_config(self, config_file_path):
        self.__logger.info("Loading configuration file...")
        with open(config_file_path, "r") as config_file:
            self.__config = json.load(config_file)
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
