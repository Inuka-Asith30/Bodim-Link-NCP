import paramiko
import time

hostname = 'ssh-bodimlink.alwaysdata.net'
username = 'bodimlink'
password = 'bodimlink@2026'

print("Connecting to AlwaysData SSH...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(hostname, username=username, password=password)
    print("Connected successfully!")
    
    commands = [
        "cd /home/bodimlink/Bodim-Link-NCP && rm -rf venv",
        "cd /home/bodimlink/Bodim-Link-NCP && /usr/alwaysdata/python/3.14/bin/python3 -m venv venv",
        "cd /home/bodimlink/Bodim-Link-NCP && source venv/bin/activate && pip install -r requirements.txt",
        "cd /home/bodimlink/Bodim-Link-NCP && echo 'from app import app as application' > wsgi.py",
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        print("Output:", stdout.read().decode())
        print("Error:", stderr.read().decode())
        
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
