.PHONY: build sdist install uninstall clean

RM = rm -rf
SETUP = python3 setup.py
FULLNAME = $(SETUP) --fullname
NAME = $(SETUP) --name

INSTALL_FILE := files.txt

FILE = $(shell $(NAME))-latest.tar.gz

default: sdist

build:
	$(SETUP) build

sdist:
	$(SETUP) sdist --formats gztar
	cp dist/$(shell $(FULLNAME)).tar.gz dist/$(FILE)

install:
	$(SETUP) install --record $(INSTALL_FILE)

uninstall:
	cat $(INSTALL_FILE) | xargs $(RM)
	$(RM) $(INSTALL_FILE)

clean:
	$(SETUP) clean --all
	$(RM) dist
	$(RM) *.egg-info
