\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{yalcv}[2022/03/11 Yet Another LaTeX CV Class]
\LoadClass{article}

\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}		
\RequirePackage[english]{babel}
\RequirePackage[default]{gillius2}
\RequirePackage{moresize}
\RequirePackage{xcolor}
\RequirePackage{etoolbox}
\RequirePackage{tikz}
\RequirePackage{tabularx}
\RequirePackage{setspace}
\RequirePackage{fontawesome5}
\RequirePackage[hidelinks]{hyperref}
\RequirePackage{bm}
\RequirePackage{silence}
\WarningFilter{etex}{Extended allocation}
\RequirePackage{worldflags}
\RequirePackage[a4paper,vmargin=5pt,hmargin=5pt]{geometry}

\pagestyle{empty}

%%% Fonts
%\renewcommand*\familydefault{\sfdefault} 
%%% Colors
\definecolor{darkboxbgcolor}{HTML}{303E4C}
\definecolor{darkboxfgcolor}{HTML}{FFFFFF}

\definecolor{lightboxbgcolor}{HTML}{BAC7CE}
\definecolor{lightboxfgcolor}{HTML}{FFFFFF}

\definecolor{bgcolor}{HTML}{FFFFFF}
\definecolor{fgcolor}{HTML}{000000}

\definecolor{gray0}{HTML}{B5BBBD}
\definecolor{gray1}{HTML}{869092}

\definecolor{accent}{HTML}{F9A620}

\pagecolor{bgcolor}

\newbool{isleft}
\setbool{isleft}{true}

%%% Lengths
\newlength{\cv@body@width}
\newlength{\cv@sidebar@gap}
\newlength{\cv@sidebar@width}
\newlength{\cv@body@height}
\newlength{\cv@footer@gap}
\newlength{\cv@footer@height}
\newlength{\icon@adjustment}

\deflength{\cv@body@width}{0.75\textwidth}
\deflength{\cv@sidebar@gap}{5pt}
\deflength{\cv@sidebar@width}{\dimexpr\textwidth-\cv@sidebar@gap-\cv@body@width-2\fboxsep\relax}
{
    \small%
    \global\deflength{\cv@footer@height}{\baselineskip}
}

\deflength{\cv@footer@gap}{0pt}
\deflength{\cv@body@height}{\dimexpr\textheight-4\fboxsep-\cv@footer@gap-\cv@footer@height\relax}
\deflength{\topskip}{0pt}
\deflength{\parindent}{0pt}

%%% New Commands
\newcounter{ii}

%% defines standard space between icon and text
\newcommand*{\cviconskip}{\;}

%% draws a single arrow pointing to the left or the right (#1)
%% using color #2
\newcommand*{\arrow}[2][left]{
    \begin{tikzpicture}[scale=0.58]
        \ifstrequal{#1}{left}{%
            \filldraw[fill=#2,draw=#2] (0,0)--(0.2,0)--(0.3,0.2)--(0.2,0.4)--(0,0.4)--(0.1,0.2)--cycle;%
        }{%
            \filldraw[fill=#2,draw=#2] (0,0.2)--(0.1,0)--(0.3,0)--(0.2,0.2)--(0.3,0.4)--(0.1,0.4)--cycle;
        }%
    \end{tikzpicture}
}

%% draws multiple arrows (n = #2) poinitng to direction #1 and color #3
\newcommand*{\narrow}[3][left]{%
    \defcounter{ii}{0}%
    \whileboolexpr{test {\ifnumless{\value{ii}}{#2}}}{%
        \stepcounter{ii}%
        \arrow[#1]{#3}%
        \ifnumless{\value{ii}}{#2}{%
            \hspace{-6pt}}{%
        }%
    }%
}

%% draws a double arrow with color #2 pointing to direction #1
\newcommand*{\doublearrow}[2][left]{%
    \narrow[#1]{2}{#2}%
}

%% draws a triple arrow with color #2 pointing to direction #1
\newcommand*{\triplearrow}[2][left]{%
    \narrow[#1]{3}{#2}%
}

%% gets the current width adjusting for the box seperators on left and right
\newcommand*{\currentwidth}{\dimexpr\linewidth-2\fboxsep\relax}

%% creates a box used for the title (#2) optionally appended by a string #1
\newcommand*{\cvheader}[2][CV]{
	\colorbox{darkboxbgcolor}{%
        \HUGE%
        \makebox(\currentwidth,\baselineskip){%
            \color{darkboxfgcolor}%
            \uppercase{#2}
				\ifblank{#1}{}{%
            	\textbullet\ 
            	\uppercase{#1}}
				}%
    }%
}

%% creates a footer box with 3 elements which are separated by a bullet point
\newcommand*{\cvfooter}[3]{
    \par%
    \nointerlineskip%
    \vspace*{\cv@footer@gap}%
    \colorbox{lightboxbgcolor}{%
        \small%
        \makebox(\currentwidth,\cv@footer@height){%
            \color{lightboxfgcolor}%
            #1 \textbullet\
            #2 \textbullet\
            #3%
        }%
    }%
}

%% creates a section title wiht text #2 in the main body optionally prepended by
%% #1 (typically and icon or arrows)
\newcommand*{\cvbodysection}[2][]{
    \par%
    \colorbox{darkboxbgcolor}{%
        \makebox(\currentwidth,\baselineskip)[l]{%
            \color{darkboxfgcolor}%
            \ifblank{#1}{}{#1\ }%
            \textbf{%
                \uppercase{#2}%
            }%
        }%
    }%
    \medskip%
}

%% creates a section in the sidebar with title #1
\newcommand*{\cvsidebarsection}[1]{
    \centering{
        \large{%
            \uppercase{#1}%
        }%
        \par
        \rule[.5\baselineskip]{.7\currentwidth}{0.4pt}%
        \par%
        \vspace{-\medskipamount}
    }%    
}

%% creates a quote (#1) surrounded by 2 double arrows
\newcommand*{\cvquote}[1]{%
    \parbox{\currentwidth}{%
        \begin{quote}
            \doublearrow{gray0}%
            #1%
            \doublearrow[right]{gray0}%
        \end{quote}%
    }%
}

\DeclareListParser*{\for@nl@list}{\\}

%% creates an entry for the CV with:
%% #1: Period, e.g. 2020/01 -- current
%% #2: Jobtitle, e.g. Data Scientist
%% #3: Employer
%% #4: A list of items separated by \\ which are then put into an itemize env
\newcommand{\cventry}[4]{%
    \renewcommand{\labelitemi}{\arrow{gray1}}
    \begin{tabularx}{\currentwidth}{Xlcl}
        \textbf{#2} & \textcolor{accent}{#3} & \textcolor{gray0}{\textbullet} & \textcolor{gray1}{#1}
    \end{tabularx}
    \textcolor{gray0}{\hrule}
    \begin{itemize}
        \deflength{\itemsep}{0pt}
        \for@nl@list{\item}{#4}
    \end{itemize}
}

%% creates a fontawesome #2 icon with the given color #1
\newcommand*{\cvicon}[2][]{%
    {%
        \ifstrempty{#1}{}{\color{#1}}%
        \faIcon{#2}%
    }%
}

%% aligns text #3 and a fontawesome icon #2 with the given color #1 vertically
\newcommand*{\cv@text@aligned@icon}[3][]{%
    \setbox0\hbox{#3}
    \setbox1\hbox{\cvicon[#1]{#2}}
    \deflength{\icon@adjustment}{\dimexpr\ht0-\ht1\relax}
    \raisebox{\dimexpr\icon@adjustment/2\relax}{\cvicon[#1]{#2}}
}

%% creates an fontawesom icon #2 
\newcommand*{\cvicontext}[3][]{%
    \cv@text@aligned@icon[#1]{#2}{#3}\cviconskip#3%
}

\newcommand*{\cviconlink}[4][]{%
    \cv@text@aligned@icon[#1]{#2}{#3}\cviconskip\href{#4}{#3}
}

\newcommand*{\cviconemail}[4][]{%
    \cv@text@aligned@icon[#1]{#2}{#3}\cviconskip\href{mailto:#4}{#3}
}

\newcommand*{\cvlanguage}[3][7pt]{%
    \worldflag[width=#1]{#2}\cviconskip#3
}

\newcommand*{\cvrating}[5][10]{%
\begin{onehalfspace}
    \cvicontext[#5]{#4}{#3}%
    \par%
    \defcounter{ii}{0}%
    \whileboolexpr{test {\ifnumless{\value{ii}}{#1}}}{%
        \ifnumless{\value{ii}}{#2}{%
            \cvicon[accent]{star}}{%
            \cvicon{star}%
        }%
        \stepcounter{ii}%
    }%
\end{onehalfspace}%
\medskip%
}

%% Environments

\newsavebox{\sidebarbox}
\newenvironment*{cvsidebar}{%
    \ignorespaces%
    \begin{lrbox}{\sidebarbox}%
        \begin{minipage}[t][\cv@body@height][t]{\cv@sidebar@width}%
            \vspace{0pt}% need this to ensure minipages align c.f. https://bit.ly/3pioFT7
            \bigskip%
            \color{darkboxfgcolor}%
}{%
        \end{minipage}%
    \end{lrbox}%
    \colorbox{darkboxbgcolor}{%
        \usebox{\sidebarbox}%
    }%
    \ifbool{isleft}{%
        \hspace*{\cv@sidebar@gap}%
        \global\setbool{isleft}{false}%
    }{%
        \global\setbool{isleft}{true}%
    }%
    \ignorespacesafterend%
}

\newenvironment*{cvbody}{%
    \ignorespaces%
    \begin{minipage}[t][\cv@body@height][t]{\cv@body@width}%
        \vspace{-\fboxsep}%
}{%
    \end{minipage}%
    \ifbool{isleft}{%
        \hspace*{\cv@sidebar@gap}%
        \global\setbool{isleft}{false}%
    }{%
        \global\setbool{isleft}{true}%
    }%
    \ignorespacesafterend%
}

\newenvironment*{cvsidebarbox}[1][]{%
    \ignorespaces%
    \ifstrequal{#1}{b}{\vfill}{}%
    \begin{spacing}{1.5}
    \centering
}{%
    \end{spacing}
    \vspace{2\baselineskip}
    \ignorespacesafterend%
}