.PHONY: node controller

CP=cp
RM=rm -rf

default: node controller

controller:
	$(MAKE) -C $@

node:
	$(MAKE) -C $@
	$(CP) node/dist/*latest.tar.gz controller/tpycontrol/data

clean:
	$(MAKE) -C node clean
	$(RM) controller/tpycontrol/data/*latest.tar.gz
	$(MAKE) -C controller clean
