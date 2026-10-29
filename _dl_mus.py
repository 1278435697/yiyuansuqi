import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
for f in ["index-BqJJw04H.js", "MuseumView-aROHavN7.js", "TryonPlaceholder-Bp1Rhoms.js", "index-BkQVKgL5.css", "MuseumView-feyVYxtT.css", "TryonPlaceholder-BpZwNlAo.css", "exhibits-Cb5qGZIp.js"]:
    try:
        sftp.get(f"/www/wwwroot/yisu/frontend/dist/museum/assets/{f}", rf"D:\yisu-ai-platform\_dl\{f}")
        print("DL_OK", f)
    except Exception as e:
        print("DL_FAIL", f, e)
sftp.close()
cli.close()
