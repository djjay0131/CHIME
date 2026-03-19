.PHONY: pdfs serve serve-only build clean

HUGO_IMAGE = hugomods/hugo:latest
SITE_DIR   = $(shell pwd)/site

# Build both PDFs from LaTeX sources
pdfs:
	cd report && make
	cd presentation && make
	mkdir -p site/static/pdfs
	cp report/main.pdf site/static/pdfs/report.pdf
	cp presentation/main.pdf site/static/pdfs/presentation.pdf

# Serve site locally with live reload at http://localhost:1313 (rebuilds PDFs first)
# Requires: Docker running + pdflatex
serve: pdfs
	docker run --rm -it \
	  -v $(SITE_DIR):/src \
	  -p 1313:1313 \
	  $(HUGO_IMAGE) server --buildDrafts --bind 0.0.0.0

# Serve without rebuilding PDFs (faster iteration on site/content/ and site/layouts/)
# Requires: Docker running; PDFs must already be in site/static/pdfs/
serve-only:
	docker run --rm -it \
	  -v $(SITE_DIR):/src \
	  -p 1313:1313 \
	  $(HUGO_IMAGE) server --buildDrafts --bind 0.0.0.0

# Build static site for inspection (output: site/public/)
# Requires: Docker running
build: pdfs
	docker run --rm \
	  -v $(SITE_DIR):/src \
	  $(HUGO_IMAGE) hugo --minify

# Remove all build artifacts
clean:
	cd report && make clean
	cd presentation && make clean
	rm -f site/static/pdfs/*.pdf
	rm -rf site/public/
	rm -f .hugo_build.lock
