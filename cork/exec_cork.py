def perform_boolean_operation(mesh1_path, mesh2_path, operation, output_path):
  import subprocess
  import os
  import time
  import platform

  RED = '\033[91m'
  RESET = '\033[0m"'

  if operation == 'union':
    operation = '-union'
  elif operation == 'difference':
    operation = '-diff'
  elif operation == 'intersection':
    operation = '-isct'

  cwd = os.getcwd()
  if not os.path.isabs(output_path):
    output_path = os.path.join(cwd, output_path)

  import meshio
  m1 = meshio.read(mesh1_path)
  new_mesh1_path = mesh1_path[:-3] + 'off'
  m1.write(new_mesh1_path)

  m2 = meshio.read(mesh2_path)
  new_mesh2_path = mesh2_path[:-3] + 'off'
  m2.write(new_mesh2_path)

  new_output_path = output_path[:-3] + 'off'

  if platform.system() == "Windows" :
    binary_path = "wincork.exe"
  else:
    if 'CORK_ROOT_DIR' in os.environ:
      binary_path = os.path.join(os.environ["CORK_ROOT_DIR"], "bin", "cork_bin")
    else:
      binary_path = os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin", "cork", "cork_bin")
  try:
    command = [binary_path, operation, new_mesh1_path, new_mesh2_path, new_output_path]

    start_time = time.time()
    with open(os.devnull, 'w') as null_file:
      subprocess.check_call(command, stdout=null_file, stderr=null_file)
    end_time = time.time()
  except Exception as e:
    raise

  # The following is  a method to use meshio without SALOME crashing
  command = ['python3', '-c', f'import meshio; m = meshio.read("{new_output_path}"); m.write("{output_path}")']
  with open(os.devnull, 'w') as null_file:
    try:
      subprocess.check_call(command, stdout=null_file, stderr=null_file)
    except Exception as e:
      raise
  return end_time - start_time

def cork_main(operation, fn1, fn2, out_name):
  return perform_boolean_operation(fn1, fn2, operation, out_name)
