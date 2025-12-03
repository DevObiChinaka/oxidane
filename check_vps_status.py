import paramiko
import time

# VPS connection details
hostname = "169.255.57.172"
username = "root"

print("=" * 70)
print("VPS BACKEND STATUS CHECK")
print("=" * 70)

password = input("\nEnter VPS root password: ")

try:
    # Connect to VPS
    print("\n[1] Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
    print("✅ Connected to VPS")
    
    # Check if Gunicorn is running
    print("\n[2] Checking Gunicorn service status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status oxidane-gunicorn | grep -E 'Active:|Main PID'")
    output = stdout.read().decode()
    print(output)
    
    # Check what port Gunicorn is listening on
    print("\n[3] Checking Gunicorn configuration...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/systemd/system/oxidane-gunicorn.service | grep ExecStart")
    output = stdout.read().decode()
    print(output)
    
    # Check nginx configuration
    print("\n[4] Checking Nginx status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status nginx | grep -E 'Active:'")
    output = stdout.read().decode()
    print(output)
    
    # Check nginx sites configuration
    print("\n[5] Checking Nginx site configuration...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /etc/nginx/sites-enabled/")
    output = stdout.read().decode()
    print(output)
    
    # Check if port 80 is listening
    print("\n[6] Checking listening ports...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp | grep -E ':(80|443|8000)'")
    output = stdout.read().decode()
    print(output)
    
    # Check recent Gunicorn logs for errors
    print("\n[7] Checking recent Gunicorn logs...")
    stdin, stdout, stderr = ssh.exec_command("journalctl -u oxidane-gunicorn --since '5 minutes ago' --no-pager | tail -20")
    output = stdout.read().decode()
    print(output)
    
    ssh.close()
    print("\n" + "=" * 70)
    print("STATUS CHECK COMPLETE")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
