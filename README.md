meshbooleanplugin
======
Interface for performing boolean operations on meshes in SALOME

Local Tests
=======
To try the plugin locally, follow these steps:
1. Clone the repo to `$SMESH_ROOT_DIR/share/salome/plugins/smesh/`

2. Open the file located at `$SMESH_ROOT_DIR/share/salome/plugins/smesh/smesh_plugins.py`.

3. Add the following code to the end of the file:
   
```
try:
	from meshbooleanplugin.mesh_boolean_plugin import MeshBoolean
	salome_pluginsmanager.AddFunction('Boolean Mesh Operations', 'Perform boolean operations on meshes', MeshBoolean)
except Exception as e:
	salome_pluginsmanager.logger.info('ERROR: MeshBoolean plug-in is unavailable: {}'.format(e))
	pass
```
4. Create the ui.py files:
got to the root of the plugin and run `make`

5. Clone the backend codes with `./clone.sh`
   
6. Compile the project with
```
mkdir -p build
cd build
cmake ..
make
```
7. Install the Python requirements with `pip install -r requirements.txt`

How to use ?
=======
1. start salome
2. find the plugin with the other SMESH plugins
