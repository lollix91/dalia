#!/usr/bin/env bash
# PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome mmdc -i example/docs/diagrams/class.md -o class.pdf -w 800 -H 600 -s 1.2
# ./makeacademicpdf.sh example/docs/doc.md  doc.pdf
# pdflatex main.tex
# md2academicpdf.sh
#
# Convert Markdown -> academic-styled PDF using pandoc + xelatex.
# Usage:
#   ./md2academicpdf.sh input.md output.pdf [refs.bib] [csl-file]
#
# Requirements:
#   - pandoc (>=2.11 recommended)
#   - xelatex (TeX Live / MikTeX)
#   - fonts you want installed (we default to TeX Gyre Termes / Times-like)
#   - (optional) a .bib file for bibliography, optional CSL style file
#
set -euo pipefail

if ! command -v pandoc >/dev/null 2>&1; then
  echo "Error: pandoc is not installed. Please install pandoc and try again." >&2
  exit 1
fi
if ! command -v xelatex >/dev/null 2>&1; then
  echo "Error: xelatex is not installed. Please install TeX Live or MikTeX and try again." >&2
  exit 1
fi

INPUT_MD="${1:-}"
OUTPUT_PDF="${2:-}"
BIBFILE="${3:-}"
CSLFILE="${4:-}"

if [[ -z "$INPUT_MD" || -z "$OUTPUT_PDF" ]]; then
  cat <<EOF
Usage: $0 input.md output.pdf [refs.bib] [csl-file]

Converts input.md -> output.pdf with an academic theme.
Optional: provide refs.bib for bibliography and a CSL file for citation styling.
EOF
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

HEADER_TEX="$TMPDIR/header.tex"
TEMPLATE_TEX="$TMPDIR/template.tex"

cat > "$HEADER_TEX" <<'LATEX'
% ===== header.tex: academic styling injected via -H =====
\usepackage{fontspec}
\usepackage{microtype}
\usepackage{titlesec}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{sectsty}
\usepackage{hyperref}
\usepackage{bookmark}
\usepackage{csquotes}
\usepackage{framed}
\usepackage{fancyvrb}
\usepackage{color}
\definecolor{shadecolor}{RGB}{248,248,248}
\newenvironment{Shaded}{\begin{snugshade}}{\end{snugshade}}
\usepackage{fvextra}
\DefineVerbatimEnvironment{Highlighting}{Verbatim}{
  breaklines=true,          % automatically wrap long lines
  breakanywhere=true,       % wrap at any character if needed
  commandchars=\\\{\}       % for knitr syntax
}
\newcommand{\KeywordTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{\textbf{#1}}}
\newcommand{\DataTypeTok}[1]{\textcolor[rgb]{0.56,0.13,0.00}{#1}}
\newcommand{\DecValTok}[1]{\textcolor[rgb]{0.25,0.63,0.44}{#1}}
\newcommand{\BaseNTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{#1}}
\newcommand{\FloatTok}[1]{\textcolor[rgb]{0.25,0.63,0.44}{#1}}
\newcommand{\CharTok}[1]{\textcolor[rgb]{0.25,0.44,0.63}{#1}}
\newcommand{\StringTok}[1]{\textcolor[rgb]{0.25,0.44,0.63}{#1}}
\newcommand{\CommentTok}[1]{\textcolor[rgb]{0.38,0.63,0.69}{\textit{#1}}}
\newcommand{\OtherTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{#1}}
\newcommand{\AlertTok}[1]{\textcolor[rgb]{1.00,0.00,0.00}{#1}}
\newcommand{\FunctionTok}[1]{\textcolor[rgb]{0.02,0.16,0.49}{#1}}
\newcommand{\RegionMarkerTok}[1]{\textcolor[rgb]{0.50,0.50,0.50}{#1}}
\newcommand{\ErrorTok}[1]{\textcolor[rgb]{1.00,0.00,0.00}{#1}}
\newcommand{\NormalTok}[1]{#1}
\newcommand{\OperatorTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{#1}}
\newcommand{\ExtensionTok}[1]{#1}
\newcommand{\BuiltInTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{\textbf{#1}}}


% Add table packages
\usepackage{caption}
\usepackage{booktabs}
\usepackage{longtable} % ✅ Fixes "Environment longtable undefined"
\usepackage{array}
\usepackage{multirow}

% ===== header.tex: academic styling injected via -H =====
% Use fontspec for better typography (requires xelatex)
\usepackage{fontspec}
\usepackage{microtype}      % better typesetting
\usepackage{titlesec}       % control section spacing
\usepackage{setspace}       % line spacing control
\usepackage{enumitem}       % control lists
\usepackage{geometry}       % margins
\usepackage{fancyhdr}       % header/footer
\usepackage{sectsty}        % section font styles
\usepackage{hyperref}       % clickable links
\usepackage{bookmark}       % better bookmarks
\usepackage{csquotes}       % context sensitive quotes for biblatex/citeproc

% Fonts (Times-like). Change mainfont if you want a different serif.
\defaultfontfeatures{Ligatures=TeX,Scale=MatchLowercase}
\setmainfont{TeX Gyre Termes} % fallback to Times-like; change to "Times New Roman" if available
\setsansfont{TeX Gyre Heros}
\setmonofont{TeX Gyre Cursor}

% Page geometry (academic defaults)
\geometry{
  left=3cm,
  right=3cm,
  top=3cm,
  bottom=3cm,
  headheight=14pt
}

% Section numbering depth & spacing
\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{2}
\titlespacing*{\section}{0pt}{14pt}{8pt}
\titlespacing*{\subsection}{0pt}{12pt}{6pt}
\titlespacing*{\subsubsection}{0pt}{10pt}{4pt}
\allsectionsfont{\normalfont\bfseries}

% Paragraph spacing and line height
\setstretch{1.15}
\setlength{\parskip}{6pt}

% Fancy header/footer
\pagestyle{fancy}
\fancyhf{}
\rhead{\small \leftmark}
\lhead{\small \rightmark}
\rfoot{\small \thepage}

% Make links a subtle color but also ensure they print; colorlinks false to keep boxed links out
\hypersetup{
  colorlinks=true,
  linkcolor=black,
  citecolor=black,
  urlcolor=black,
  hidelinks=true,
  pdftitle={Pandoc Academic PDF},
  pdfauthor={}
}

% Numbered captions for figures/tables if used by pandoc
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}

% Allow nicer tables
\usepackage{booktabs}
% Fix for Pandoc's \tightlist (compact lists)
\providecommand{\tightlist}{%
  \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

% End header
% =====================================================
LATEX

cat > "$TEMPLATE_TEX" <<'LATEX'
\documentclass[$if(classoption)$$classoption$$endif$,$if(papersize)$$papersize$$endif$]{article}
$if(lot)$\listoftables$endif$
$if(lof)$\listoffigures$endif$
$for(header-includes)$
$header-includes$
$endfor$
\begin{document}
$if(title)$
\begin{center}
  {\Large\bfseries $title$}\\[6pt]
  $if(author)$ {\normalsize $for(author)$$author$$sep$ \\ $endfor$} \\[6pt] $endif$
  $if(date)$ {\normalsize $date$} $endif$
\end{center}
\vspace{1em}
$endif$

$if(toc)$
\newpage
$endif$

$body$

$if(bibliography)$
\newpage
\section*{References}
$if(biblio-title)$
\renewcommand{\refname}{$biblio-title$}
$endif$
\printbibliography[heading=none]
$endif$

\end{document}
LATEX

PANDOC_CMD=(pandoc "$INPUT_MD" -o "$OUTPUT_PDF" --pdf-engine=xelatex --template="$TEMPLATE_TEX" -H "$HEADER_TEX" --toc --number-sections -V geometry:margin=1in -V lang=en)

if [[ -n "$BIBFILE" ]]; then
  if [[ ! -f "$BIBFILE" ]]; then
    echo "Warning: bibliography file '$BIBFILE' not found. Ignoring bibliography." >&2
  else
    PANDOC_CMD+=(--citeproc --bibliography="$BIBFILE")
  fi
fi

if [[ -n "$CSLFILE" ]]; then
  if [[ ! -f "$CSLFILE" ]]; then
    echo "Warning: csl file '$CSLFILE' not found. Ignoring CSL." >&2
  else
    PANDOC_CMD+=("--csl=$CSLFILE")
  fi
fi

echo "Running pandoc..."
"${PANDOC_CMD[@]}"

echo "Done. Output: $OUTPUT_PDF"
