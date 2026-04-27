TEX = pdflatex
MAIN = main
V2 = main-v2

.PHONY: all presentation notes v2 v2-presentation v2-notes clean

all: presentation

presentation: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	$(TEX) $(MAIN)
	$(TEX) $(MAIN)

notes: $(MAIN)-notes.pdf

$(MAIN)-notes.pdf: $(MAIN).tex
	$(TEX) -jobname=$(MAIN)-notes "\def\SHOWNOTES{}\input{$(MAIN)}"
	$(TEX) -jobname=$(MAIN)-notes "\def\SHOWNOTES{}\input{$(MAIN)}"

v2: v2-presentation v2-notes

v2-presentation: $(V2).pdf

$(V2).pdf: $(V2).tex
	$(TEX) $(V2)
	$(TEX) $(V2)

v2-notes: $(V2)-notes.pdf

$(V2)-notes.pdf: $(V2).tex
	$(TEX) -jobname=$(V2)-notes "\def\SHOWNOTES{}\input{$(V2)}"
	$(TEX) -jobname=$(V2)-notes "\def\SHOWNOTES{}\input{$(V2)}"

clean:
	rm -f $(MAIN).pdf $(MAIN)-notes.pdf $(V2).pdf $(V2)-notes.pdf \
	  $(MAIN).aux $(MAIN).log $(MAIN).nav $(MAIN).out $(MAIN).snm $(MAIN).toc $(MAIN).vrb \
	  $(MAIN)-notes.aux $(MAIN)-notes.log $(MAIN)-notes.nav $(MAIN)-notes.out $(MAIN)-notes.snm $(MAIN)-notes.toc $(MAIN)-notes.vrb \
	  $(V2).aux $(V2).log $(V2).nav $(V2).out $(V2).snm $(V2).toc $(V2).vrb \
	  $(V2)-notes.aux $(V2)-notes.log $(V2)-notes.nav $(V2)-notes.out $(V2)-notes.snm $(V2)-notes.toc $(V2)-notes.vrb
