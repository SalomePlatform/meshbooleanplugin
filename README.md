MeshBooleanPlugin
======
Interface for performing boolean operations on meshes in SALOME

Local Tests
=======
To try the plugin locally, follow these steps:

1. Open the file located at `$SMESH_ROOT_DIR/share/salome/plugins/smesh/smesh_plugins.py`.

2. Add the following code to the end of the file:
   
```
try:
	from MeshBooleanPlugin.mesh_boolean_plugin import MeshBoolean
	salome_pluginsmanager.AddFunction('Boolean Mesh Cutting', 'Perform boolean operations on meshes', MeshBoolean)
except Exception as e:
	salome_pluginsmanager.logger.info('ERROR: MeshBoolean plug-in is unavailable: {}'.format(e))
	pass
```

How to use ?
=======
1. run the command 'make' (this generates the ui python file)
2. start salome
3. find the plugin with the other SMESH plugins
