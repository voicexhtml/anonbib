
PYTHON=python2

all:
	$(PYTHON) writeHTML.py

clean:
	rm -f *~ */*~ *.pyc *.pyo

veryclean: clean
	rm -f author.html date.html topic.html bibtex.html tmp.bib
