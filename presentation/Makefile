TEX = pdflatex
MAIN = main

.PHONY: all clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	$(TEX) $(MAIN)
	$(TEX) $(MAIN)

clean:
	rm -f $(MAIN).pdf $(MAIN).aux $(MAIN).log $(MAIN).nav $(MAIN).out $(MAIN).snm $(MAIN).toc $(MAIN).vrb
