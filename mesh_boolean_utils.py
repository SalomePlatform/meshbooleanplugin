import os
import subprocess
import sys

def execCommand(command, waitUntilFinished=False):
  """
  Run a command
  Print output in real time
  """
  print("Executing: ", " ".join(command))
  try:
    process = subprocess.Popen(
        command,
        shell=False, # needed for meshio to run in SALOME environment
        encoding='utf-8',
        errors='replace'
    )
    if waitUntilFinished:
      process.wait()
  except Exception as e:
    raise
  return process

def meshIOConvert(file_in, file_out):
  """
  Convert files with meshio
  """
  command = ['python3', '-c', f'import meshio; m = meshio.read(r"{file_in}"); m.write(r"{file_out}")']
  #command = ['meshio', 'convert', file_in, file_out]
  execCommand(command, waitUntilFinished=True)
  if os.path.getsize(file_out) == 0:
    raise RuntimeError(f"Error in meshio convert. {file_out} is void")
