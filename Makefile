UI_FILES := $(wildcard *.ui)
PY_FILES := $(UI_FILES:.ui=_ui.py)

all: $(PY_FILES)

%_ui.py: %.ui
	pyuic5 $< -o $@

clean:
	rm -f $(PY_FILES)

.PHONY: all clean

