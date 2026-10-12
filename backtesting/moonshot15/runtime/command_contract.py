"""## Executive summary (read this first)
Reject missing Docker option values before invoking a container; no forecast changes.
"""
def validate_docker_argv(args):
    if len(args)<2 or args[:2]!=['docker','run']:return
    value_options={'-e','--env','-v','--volume','--user','--network','--memory','--cpus','--tmpfs','--cap-drop','--security-opt','--pids-limit','--ulimit','--entrypoint','--name'}
    for i,arg in enumerate(args):
        if arg in value_options and (i+1>=len(args) or str(args[i+1]).startswith('-')):
            raise ValueError('missing Docker option value: '+arg)
