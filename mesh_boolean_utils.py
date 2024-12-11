import os
import subprocess
import sys

def execCommand(command):
  """
  Run a command
  Print output in real time
  """
  print("Executing: ", " ".join(command))
  try:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False, # needed for meshio to run in SALOME environment
        encoding='utf-8',
        errors='replace'
    )
    while True:
      realtime_output = process.stdout.readline()
      if realtime_output == '' and process.poll() is not None:
        break
      if realtime_output:
        print(realtime_output.strip(), flush=True)
  except Exception as e:
    raise

def meshIOConvert(file_in, file_out):
  """
  Convert files with meshio
  """
  command = ['python3', '-c', f'import meshio; m = meshio.read("{file_in}"); m.write("{file_out}")']
  #command = ['meshio', 'convert', file_in, file_out]
  execCommand(command)
  if os.path.getsize(file_out) == 0:
    raise RuntimeError(f"Error in meshio convert. {file_out} is void")
