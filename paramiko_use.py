import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname='120.26.175.79',port=22,username='root',password='AAAAaaaa0'
)
stdin, stdout, stderr = client.exec_command('ls')
print(stdout.read().decode('utf-8'))