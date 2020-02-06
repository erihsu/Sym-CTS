all:
	cd symcts
	python3 flow.py
	cd ..
	mkdir workspace & cd workspace
	cp ../evaluation/extract.pl .
	cp ../evaluation/input/ispd09f11 .
	cp ../library/tech/45nm_LP.pm .
	cp ../library/spice/* .
	perl perl extract.pl ispd09f11 result 45nm_LP.pm
clean:
	rm -f workspace/*
	rm -f library/spice/*
	rm -f library/lib/*