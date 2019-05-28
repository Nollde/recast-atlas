import os
import yaml

def get_file(filename, backend, load_yaml = False):
    if backend == 'local':
        return yaml.load(open(filename))
    elif backend == 'kubernetes':
        from kubernetes import config as k8sconfig 
        from kubernetes import client as k8sclient  
        k8sconfig.load_kube_config()
        r,_,_ = k8sclient.ApiClient().call_api('/api/v1/namespaces/default/services/fileaccess/proxy/{}'.format(filename),'GET', _preload_content = False)    
        contents = r.read().decode('ascii')

        if load_yaml:
            return yaml.load(contents)
        return contents

def extract_results(resultspec, dataarg, backend):
    results = []
    for r in resultspec:
        filename = os.path.join(dataarg,r['relpath'])
        results.append(
            {'name': r['name'], 'value': get_file(filename, backend, r.get('load_yaml',False))}
        )
    return results
