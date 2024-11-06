import requests
import time
import subprocess
import allure
import json
import pytest

URL = "http://0.0.0.0:8069/respond"

@allure.description("""BLEU test""")
