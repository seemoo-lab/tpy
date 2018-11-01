.PHONY: build sdist install uninstall clean

RM = rm -rf
SETUP = python3 setup.py

INSTALL_FILE := files.txt

default: build sdist install

build:
	$(SETUP) build

sdist:
	$(SETUP) sdist

install:
	$(SETUP) install --record $(INSTALL_FILE)

uninstall:
	cat $(INSTALL_FILE) | xargs $(RM)
	$(RM) $(INSTALL_FILE)

clean:
	$(SETUP) clean --all
	$(RM) dist
	$(RM) *.egg-info
