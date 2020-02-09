all:
	mkdir $(SYMCTS)/workspace
	mkdir $(SYMCTS)/evaluation/input
	mkdir $(SYMCTS)/evaluation/output
	python3 $(SYMCTS)/utils/convert_circuits.py
	python3 $(SYMCTS)/symcts/flow.py
	cp $(SYMCTS)/utils/extract.pl $(SYMCTS)/workspace
	cp $(SYMCTS)/utils/view.pl $(SYMCTS)/workspace
	cp $(SYMCTS)/utils/evaluation.py $(SYMCTS)/workspace
	cp $(SYMCTS)/evaluation/input/ispd09f11 $(SYMCTS)/workspace
	cp $(SYMCTS)/evaluation/output/result $(SYMCTS)/workspace
	cp $(SYMCTS)/library/tech/45nm_LP.pm $(SYMCTS)/workspace
	cp $(SYMCTS)/library/spice/* $(SYMCTS)/workspace
clean:
	rm -rf workspace
	rm -rf $(SYMCTS)/evaluation/input
	rm -rf $(SYMCTS)/evaluation/output
