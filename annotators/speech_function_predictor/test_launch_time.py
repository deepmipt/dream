import sys
import time
import json
import requests


SERVICE_PORT = 8107
URL = f"http://0.0.0.0:{SERVICE_PORT}"
MODEL_URL = f"{URL}/respond"

test_data = {'funcs': ['Open.Attend']}

def parse_time(real_time_str):
    real_time_str = real_time_str.replace(',', '.')
    if 'm' in real_time_str:
        minutes, seconds = real_time_str.split('m')
        total_seconds = int(minutes) * 60 + float(seconds.replace('s', ''))
    else:
        total_seconds = float(real_time_str.replace('s', ''))
    
    return total_seconds

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_launch_time.py <real_time>")
        sys.exit(1)
    
    real_time_str = sys.argv[1]
    docker_time_seconds = parse_time(real_time_str)
    
    print("Docker-compose execution time in seconds:", docker_time_seconds)
    return docker_time_seconds
    


def test_launch_time(docker_time, test_data):
    start_time = time.time()
    requests.post(MODEL_URL, json=test_data)
    total_time = time.time() - start_time
    print(f"Execution Time: {total_time} s")
    launch_time = docker_time + float(total_time)
    assert launch_time < 600, f"Expected time should be less 20 mins, but got {total_time}s"
    print(f'Total launch time:{launch_time}')

if __name__ == "__main__":
    docker_time = main()
    test_launch_time(docker_time, test_data)