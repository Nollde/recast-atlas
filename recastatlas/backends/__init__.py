import click
import json
import logging
import subprocess
import os
import base64
import textwrap

from ..config import config
log = logging.getLogger(__name__)

def run_sync(name, spec, backend):
    assert backend in ['local','docker']
    if backend == 'local':
        backend_config = config.backends[backend]['fromstring']
        from yadage.utils import setupbackend_fromstring
        from yadage.steering_api import run_workflow
        spec['backend']  = setupbackend_fromstring(backend_config,spec.pop('backendopts',{}))
        
        try:
            run_workflow(**spec)
        except:
            log.exception('caught exception')
            exc = click.exceptions.ClickException(
                click.style("Workflow failed", fg='red')
            )
            exc.exit_code = 1
            raise exc
    elif backend == 'docker':
        cwd = os.getcwd()
        image = config.backends[backend]['image']
        command = [
            'docker',
            'run',
            '--rm',
            '-i',
            '-v','{}:{}'.format(cwd,cwd),
            '-w',cwd,
            '-v','/var/run/docker.sock:/var/run/docker.sock',
            '-e','PACKTIVITY_AUTH_LOCATION={}'.format(config.backends[backend]['auth_location']),
            '-e','YADAGE_SCHEMA_LOAD_TOKEN={}'.format(config.backends[backend]['private_token']),
            '-e','YADAGE_INIT_TOKEN={}'.format(config.backends[backend]['private_token']),
            image
        ]
        dockerconfig = {}
        if config.backends[backend]['reg']['host']:
            dockerconfig = {
                "auths": {
                    "gitlab-registry.cern.ch": {
                        "auth": base64.b64encode('{}:{}'.format(
                            config.backends[backend]['reg']['user'],
                            config.backends[backend]['reg']['pass'],
                        ))}
                }
            }

        script = '''\
        mkdir -p ~/.docker
        echo '{dockerconfig}' > ~/.docker/config.json 
        cat << 'EOF' | yadage-run -f - 
        {spec}
        EOF
        '''.format(
            spec = json.dumps(spec),
            dockerconfig = json.dumps(dockerconfig) 
        )
        command += ['sh','-c',textwrap.dedent(script)]          
        subprocess.check_call(command)
        
def run_async(name, spec, backend):
    assert backend == 'kubernetes'
    if backend == 'kubernetes':
        workflow = {
            'apiVersion': 'yadage.github.io/v1',
            'kind': 'Workflow',
            'metadata': {'name': name},
            'spec': spec
        }
        from kubernetes import client as k8sclient
        from kubernetes import config as k8sconfig
        k8sconfig.load_kube_config()
        _,rc,_ = k8sclient.ApiClient().call_api('/apis/yadage.github.io/v1/namespaces/default/workflows','POST', body = workflow) 
        return rc

def check_async(name, backend):
    assert backend == 'kubernetes'
    from kubernetes import client as k8sclient
    from kubernetes import config as k8sconfig
    k8sconfig.load_kube_config()
    a,rc,d = k8sclient.ApiClient().call_api(
        '/apis/yadage.github.io/v1/namespaces/default/workflows/{}'.format(name),
        'GET',
        _preload_content = False
    ) 
    try:
        status = json.loads(a.read())['status']['workflow']
    except:
        return {'status': 'UNKNOWN'}

    if status.get('succeeded')==1:
        return {'status': 'SUCCEEDED'}
    if status.get('active')==1:
        return {'status': 'INPROGRESS'}
    if status.get('failed')==1:
        return {'status': 'FAILED'}
    return {'status': 'UNKNOWN'}

def check_backend(backend):
    if backend == 'kubernetes':
        try:
            from kubernetes import client as k8sclient
            from kubernetes import config as k8sconfig
            k8sconfig.load_kube_config()
            _,rc,_ = k8sclient.ApiClient().call_api('/apis/yadage.github.io/v1/namespaces/default/workflows','GET')
            return rc == 200
        except k8sclient.rest.ApiException:
            pass
        return False
    if backend == 'local':
        try:
            import yadage
            rc = subprocess.check_call(['docker','info'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            return rc == 0
        except:
            pass
        return False
    if backend == 'docker':
        try:
            rc = subprocess.check_call(['docker','info'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            return rc == 0
        except:
            pass
        return False

def install_backend(backend):
    pass