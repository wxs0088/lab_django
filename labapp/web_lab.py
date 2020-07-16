from subprocess  import Popen,PIPE
import threading
from rest_framework.views import APIView
def runPopen(job):
    """
    执行命令,返回popen
    """
    path = os.path
    Path = path.abspath(path.join(BASE_DIR, path.pardir))
    script_path = path.abspath(path.join(Path,'run.sh'))
    cmd = "sh %s %s" % (script_path, job)
    return Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
 
def runScript(job):
    channel_layer = get_channel_layer()
    group_name = "job_%s" % job
 
    popen = runPopen(job)
    while True:
        output = popen.stdout.readline()
        if output == '' and popen.poll() is not None:
            break
 
        if output:
            output_text = str(output.strip())
            async_to_sync(
                channel_layer.group_send
                )(
                    group_name, 
                    {"type": "job.message", "text": output_text}
                )
        else:
            err  = popen.stderr.readline()
            err_text = str(err.strip())
            async_to_sync(
                channel_layer.group_send
                )(
                    group_name,
                    {"type": "job.message", "text": err_text}
                )
            break
 
class StartJob(APIView):  
    def get(self, request, job=None):
        run =  threading.Thread(target=runScript, args=(job,))
        run.start()
        return HttpResponse('ok')