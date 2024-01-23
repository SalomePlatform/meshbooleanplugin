OUTPUT_FILES := $(wildcard **/*_output.*)
all:
	mkdir -p samples
	${SALOME_ROOT_DIR}/../../salome shell gen_meshes.py

delete_gen:
	rm -r samples

clean:
	if [ -n "$(OUTPUT_FILES)" ]; then rm $(OUTPUT_FILES); fi
	if [ -e "logs.txt" ]; then rm logs.txt; fi


.PHONY: all clean
