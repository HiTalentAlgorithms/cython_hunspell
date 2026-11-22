import os


def detect_cpus():
    return os.cpu_count() or 1
