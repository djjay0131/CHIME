TEX = pdflatex
MAIN = main

.PHONY: all presentation notes clean

all: presentation

presentation: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	$(TEX) $(MAIN)
	$(TEX) $(MAIN)

notes: $(MAIN)-notes.pdf

$(MAIN)-notes.pdf: $(MAIN).tex
	$(TEX) -jobname=$(MAIN)-notes "\def\SHOWNOTES{}\input{$(MAIN)}"
	$(TEX) -jobname=$(MAIN)-notes "\def\SHOWNOTES{}\input{$(MAIN)}"

clean:
	rm -f $(MAIN).pdf $(MAIN)-notes.pdf \
	  $(MAIN).aux $(MAIN).log $(MAIN).nav $(MAIN).out $(MAIN).snm $(MAIN).toc $(MAIN).vrb \
	  $(MAIN)-notes.aux $(MAIN)-notes.log $(MAIN)-notes.nav $(MAIN)-notes.out $(MAIN)-notes.snm $(MAIN)-notes.toc $(MAIN)-notes.vrb
