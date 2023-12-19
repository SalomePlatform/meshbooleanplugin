def perform_boolean_operation(mesh1_path, mesh2_path, operation, output_path):
    import subprocess
    import os
    import sys
    import time
    RED = '\033[91m'
    RESET = '\033[0m"'

    cwd = os.getcwd()
    if not os.path.isabs(output_path):
        output_path = os.path.join(cwd, output_path)
    new_output_path = os.path.splitext(output_path)[0] + ".obj"
    try:
        command = ["./mcut/CSGBoolean"]
        if operation == "union":
            operation = "-u"
        elif operation == "intersection":
            operation = "-i"
        elif operation == "difference":
            operation = "-ds"

        command += [mesh1_path, mesh2_path, operation, new_output_path]
        start_time = time.time()
        with open(os.devnull, 'w') as null_file:
            subprocess.check_call(command, stdout=null_file, stderr=null_file)
        end_time = time.time()

    except Exception as e:
        os.chdir(cwd)
        return -1

    print(new_output_path, output_path)
    # The following is  a method to use meshio without SALOME crashing
    command = ['python3', '-c', f'import meshio; m = meshio.read("{new_output_path}"); m.write("{output_path}")']
    with open(os.devnull, 'w') as null_file:
      try:
        subprocess.check_call(command, stdout=null_file, stderr=null_file)
      except Exception as e:
        return -1
    return end_time - start_time

def mcut_main(operation, fn1, fn2, out_name):
    return perform_boolean_operation(fn1, fn2, operation, out_name)
