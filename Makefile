#----------------------------------------------------------------------------------------
# This section in Makefile defines version  variables for various  libraries used in the
# project. These variables specify the versions of external dependencies used during the
# build process.
#----------------------------------------------------------------------------------------

# Define the version of CGAL library
CGAL_VERSION=5.6

# Define the version of IGL library
LIBIGL_VERSION=2.5.0

# Define the version of CORK library
CORK_VERSION=master

# Define the version of MCUT library
MCUT_VERSION=1.2.0

# Define the version of IRMB library
IRMB_VERSION=main


# Define commands to download library source code archives
CGAL_DOWNLOAD   = wget -c  https://github.com/CGAL/cgal/archive/refs/tags/v$(CGAL_VERSION).tar.gz -O ./cgal/cgal-$(CGAL_VERSION).tar.gz
LIBIGL_DOWNLOAD = wget -c  https://github.com/libigl/libigl/archive/refs/tags/v$(LIBIGL_VERSION).tar.gz -O ./libigl/libigl-$(LIBIGL_VERSION).tar.gz
CORK_DOWNLOAD   = wget -c  https://github.com/gilbo/cork/archive/refs/heads/$(CORK_VERSION).tar.gz -O ./cork/cork-$(CORK_VERSION).tar.gz
MCUT_DOWNLOAD   = wget -c  https://github.com/cutdigital/mcut/archive/refs/tags/v$(MCUT_VERSION).tar.gz -O ./mcut/mcut-$(MCUT_VERSION).tar.gz
IRMB_DOWNLOAD   = wget -c   https://github.com/gcherchi/InteractiveAndRobustMeshBooleans/archive/refs/heads/$(IRMB_VERSION).tar.gz -O ./irmb/irmb-$(IRMB_VERSION).tar.gz


# List of targets to be executed
LIST_MAKE_EXECUTE = \
  download-dependencies \
  cgal-build   \
  libigl-build \
  cork-build   \
  mcut-build   \
  irmb-build



# Target to download the required source code for libraries and dependencies
download-dependencies:
	@if [ ! -f ./cgal/cgal-$(CGAL_VERSION).tar.gz ]; then \
		$(CGAL_DOWNLOAD); \
	fi
	@if [ ! -f ./libigl/libigl-$(LIBIGL_VERSION).tar.gz ]; then \
		$(LIBIGL_DOWNLOAD); \
	fi
	@if [ ! -f ./cork/cork-$(CORK_VERSION).tar.gz ]; then \
		$(CORK_DOWNLOAD); \
	fi
	@if [ ! -f ./mcut/mcut-$(MCUT_VERSION).tar.gz ]; then \
		$(MCUT_DOWNLOAD); \
	fi
	@if [ ! -f ./irmb/irmb-$(IRMB_VERSION).tar.gz ]; then \
		$(IRMB_DOWNLOAD); \
	fi

cgal-build:
	@echo ""
	@echo "*============================================================*"
	@echo "  Now compiling CGAL for you, please be patient:"
	@echo "*============================================================*"
	@echo ""
	@echo "*---------------------------------*"
	@echo "   Untarring cgal-$(CGAL_VERSION).tar.gz"
	@echo "*---------------------------------*"
	if [ ! -d "cgal/cgal" ]; then \
		cd cgal && \
		tar -xf cgal-$(CGAL_VERSION).tar.gz && \
		mv cgal-$(CGAL_VERSION) cgal; \
	else \
		echo "CGAL directory already exists, skipping untar operation."; \
	fi

libigl-build:
	@echo ""
	@echo "*============================================================*"
	@echo "  Now compiling libigl for you be patient:"
	@echo "*============================================================*"
	@echo ""
	@echo "*---------------------------------*"
	@echo "   untaring libigl-$(LIBIGL_VERSION).tar.gz"
	@echo "*---------------------------------*"
	if [ ! -d "libigl/libigl" ]; then \
		cd libigl    && \
		[ ! -d "libigl" ]  && tar -xf libigl-$(LIBIGL_VERSION).tar.gz && \
		mv libigl-$(LIBIGL_VERSION) libigl ; \
	else \
		echo "libigl directory already exists, skipping untar operation."; \
	fi

cork-build:
	@echo ""
	@echo "*============================================================*"
	@echo "  Now compiling cork for you be patient:"
	@echo "*============================================================*"
	@echo ""
	@echo "*---------------------------------*"
	@echo "   untaring cork-$(CORK_VERSION).tar.gz"
	@echo "*---------------------------------*"
	if [ ! -d "cork/cork" ]; then \
		cd cork    && \
		[ ! -d "cork" ]  && tar -xf cork-$(CORK_VERSION).tar.gz && \
		mv cork-$(CORK_VERSION) cork  ; \
	else \
		echo "cork directory already exists, skipping untar operation."; \
	fi

mcut-build:
	@echo ""
	@echo "*============================================================*"
	@echo "  Now compiling mcut for you be patient:"
	@echo "*============================================================*"
	@echo ""
	@echo "*---------------------------------*"
	@echo "   untaring mcut-$(MCUT_VERSION).tar.gz"
	@echo "*---------------------------------*"
	if [ ! -d "mcut/mcut" ]; then \
		cd mcut    && \
		[ ! -d "mcut" ]  && tar -xf mcut-$(MCUT_VERSION).tar.gz && \
		mv mcut-$(MCUT_VERSION) mcut  ; \
	else \
		echo "mcut directory already exists, skipping untar operation."; \
	fi

irmb-build:
	@echo ""
	@echo "*============================================================*"
	@echo "  Now compiling irmb for you be patient:"
	@echo "*============================================================*"
	@echo ""
	@echo "*---------------------------------*"
	@echo "   untaring irmb-$(IRMB_VERSION).tar.gz"
	@echo "*---------------------------------*"
	if [ ! -d "irmb/irmb" ]; then \
		cd irmb    && \
		[ ! -d "irmb" ]  && tar -xf irmb-$(IRMB_VERSION).tar.gz && \
		mv InteractiveAndRobustMeshBooleans-$(IRMB_VERSION) irmb  ; \
	else \
		echo "irmb directory already exists, skipping untar operation."; \
	fi


UI_FILES := $(wildcard *.ui)
PY_FILES := $(UI_FILES:.ui=_ui.py)

all: $(PY_FILES) $(LIST_MAKE_EXECUTE)

%_ui.py: %.ui
	pyuic5 $< -o $@

clean:
	rm -f $(PY_FILES)

.PHONY: all clean

