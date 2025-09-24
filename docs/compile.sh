#!/usr/bin/env bash

PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome mmdc -i ../example/docs/diagrams/class.md -o class.pdf -w 800 -H 600 -s 1.2
PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome mmdc -i ../example/docs/diagrams/sequence.md -o sequence.pdf -w 800 -H 600 -s 1.2
./md2pdfedu.sh ../example/docs/doc.md  doc.pdf
./md2pdfedu.sh ../README.md  readme.pdf
./md2pdfedu.sh ./compatibility.md  compatibility.pdf
pdflatex main.tex
pdfunite main.pdf readme.pdf compatibility.pdf doc.pdf class-1.pdf sequence-1.pdf dalia.pdf
rm -rf main.pdf readme.pdf compatibility.pdf doc.pdf class-1.pdf sequence-1.pdf *.aux *.log *.out