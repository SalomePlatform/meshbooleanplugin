mmgplugin
======
MMG (Mesh Adaptation Kernel) Interface for SALOME

Local Tests
=======
To try the plugin locally, follow these steps:

1. Open the file located at `$SMESH_ROOT_DIR/share/salome/plugins/smesh/mmgplugin/smesh_plugins.py`.

2. Add the following code to the end of the file:
   
```
   try:
	   from mmgplugin.mmgPlug_plugin import Mmg
	   salome_pluginsmanager.AddFunction('ReMesh with MMG', 'Run MMG', Mmg)
   except Exception as e:
	   salome_pluginsmanager.logger.info('ERROR: MMG plug-in is unavailable: {}'.format(e))
	   pass
```

How to use ?
=======
1. run the command 'make' (this generates the ui python file)
2. start salome
3. find the plugin with the other SMESH plugins
