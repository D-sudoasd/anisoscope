---
title: 'AnisoScope: A desktop application for crystal elastic anisotropy analysis'
tags:
  - Python
  - materials science
  - elastic tensor
  - elastic anisotropy
  - scientific visualization
authors:
  - name: Delun Gong
    orcid: 0000-0001-7877-7707
    affiliation: 1
    corresponding: true
affiliations:
  - name: Institute of Metal Research, Chinese Academy of Sciences, Shenyang, China
    index: 1
    ror: 03pa1rf77
date: 12 August 2026
bibliography: paper.bib
---

# Summary

Elastic constants describe how a crystal deforms under small loads, but they
are usually exchanged as a dense table whose convention and directional
consequences are difficult to inspect.
AnisoScope is a Python desktop application and numerical library that converts
an explicit stiffness tensor represented as a 6×6 Voigt matrix into stability
diagnostics, scalar elastic averages, direction-dependent properties, plots,
and reusable tables. Analysis packages record the input matrix, unit, crystal
system, and sampling settings; figure and animation sidecars also record
relevant plotting choices. AnisoScope is intended for materials
researchers who need an inspectable step between measured or calculated elastic
constants and figures or tabular data for further analysis. It analyses the
supplied tensor but does not establish its physical provenance or applicability
to a particular specimen or calculation.

# Statement of need

The elastic response of an anisotropic crystal cannot generally be summarized
by one Young's modulus or Poisson ratio. Before anisotropy can be inspected, a
stiffness tensor must be interpreted under a stated index and shear convention,
checked for mechanical stability and numerical conditioning, inverted to obtain
compliance, and sampled over directions [@nye1985; @mouhat2014]. When these
operations are distributed across spreadsheets, short scripts, plotting tools,
and copied figures, silent symmetrization, an omitted factor of two in shear
strain, or an undocumented sampling grid can make results difficult to inspect
and reproduce.

AnisoScope provides a local workflow that accepts the full matrix, retains
detectable asymmetry, evaluates numerical, crystal-system, and implemented Born
diagnostics, calculates Voigt--Reuss--Hill estimates [@hill1952] and the universal
anisotropy index [@ranganathan2008], and samples directional Young's modulus,
linear compressibility, shear modulus, and Poisson ratio. It is for experimental
and computational materials researchers who already have a stiffness tensor and
need interactive inspection with machine-readable outputs. The software accepts
values in GPa using Voigt order `[11, 22, 33, 23, 13, 12]` and the engineering
shear strain convention. AnisoScope is a post-processing tool rather than a
first-principles calculator or materials database, and users remain responsible
for the source convention and physical applicability of the input constants.

# State of the field

Several open-source packages already analyse and visualise anisotropic elastic
properties. ElAM introduced
tensor operations and two- and three-dimensional representations of anisotropic
elastic properties [@marmier2010]. ELATE provides closely related directional
analysis through an open-source Python module and an interactive web application
[@gaillac2016]. MechElastic extends the workflow toward parsing first-principles
outputs, bulk and two-dimensional materials, stability tests, and
equation-of-state analysis [@singh2021]. ElATools and
VELAS provide broader command-line or graphical environments with multiple
mechanical descriptors, visualisations, and links to computed materials data
[@yalameha2022; @ran2023].
pymatgen supplies programmable tensor objects and analysis within a larger
materials toolkit [@ong2013]. de Jong et al. reported a 2015 Materials Project
elastic dataset for 1,181 inorganic compounds
[@dejong2015].

AnisoScope complements these broader frameworks with a local PySide6 desktop
workflow in which users can edit a complete matrix, retain detectable input
asymmetry, inspect the convention and diagnostics beside the results, and export
the matrix with the sampling settings; figure and animation sidecars additionally
record relevant rendering settings. This desktop-first
interaction model differs from ELATE's web interface, pymatgen's programmable
library workflow, and tools centered on parsing first-principles output. Keeping
the editor, diagnostics, figure controls, and export manifest in one application
motivated a focused implementation rather than an extension to a parser or web
service. The trade-off is a local Qt/VTK dependency stack and no simulation-output
parsers or database access.

# Software design

AnisoScope separates the numerical core from interface state and rendering, as
shown in \autoref{fig:architecture}. `ElasticTensor` stores the supplied matrix,
constructs its compliance, and evaluates scalar and directional quantities.
Physical stress tensors are converted to Voigt form and the resulting
engineering strain vector is converted back to a symmetric strain tensor. This
conversion makes the shear convention explicit and is tested against an exactly isotropic
analytic case. The stability service reports symmetry, invertibility,
conditioning, positive definiteness, selected crystal-system relations, and the
applicable implemented Born inequalities as separate diagnostics. For monoclinic
and triclinic inputs, the diagnostics include positive definiteness but do not
validate the source's axis and sign convention.

Sampling objects hold both directions and calculated values for a path, plane,
or sphere. Plotting and exporting consume those objects without re-evaluating
the tensor. Direct shear-modulus and Poisson-ratio calls require a transverse
direction; the sampling helpers generate an orthogonal transverse basis. For
shear-modulus and Poisson-ratio samples, the default value at each loading
direction is the discrete arithmetic mean of a 72-point transverse scan, not a
transverse extremum. Young's modulus and linear compressibility do not use this
scan.

The GUI coordinates matrix input, analysis, plot selection, and export; the
numerical calculations reside in the core library. Static figures can be
exported with Matplotlib when PyVista/VTK is unavailable. Individual
sampled-data, figure, and animation exports are accompanied by a sidecar
manifest containing the program version, complete input matrix, unit, crystal
system, and sampling grid. For shear and Poisson-ratio sampling, the sidecar
also records the transverse aggregation and transverse sample count; figure and
animation sidecars add relevant visual settings. A detached figure or CSV
retains the assumptions needed for interpretation when kept with its sidecar.

![AnisoScope data flow and desktop workflow. (a) A supplied 6 × 6 stiffness matrix enters the numerical core while an independent diagnostic view evaluates symmetry, invertibility, conditioning, positive definiteness, and the applicable implemented crystal-system relations and Born criteria. Scalar Voigt–Reuss–Hill averages are reported separately from directional properties evaluated from the compliance matrix along paths, planes, or spheres; all branches can feed manifest-backed outputs. (b) The desktop workflow separates tensor entry and convention confirmation, analysis, directional inspection, and export. The application derives quantities from the supplied tensor but does not establish its physical provenance or applicability.\label{fig:architecture}](figures/architecture_workflow.png){ width=100% }

The desktop interface presents the matrix and convention alongside diagnostics
and summary results
(\autoref{fig:interface}).

![Interface state after loading the bundled `Si cubic` demonstration matrix and running the standard analysis. (a) The input panel exposes the GPa unit, crystal system, Voigt ordering, and matrix entries. (b) The dashboard reports the implemented diagnostics and Hill averages. These constants are used only for interface and regression examples, not as reference data.\label{fig:interface}](figures/anisoscope_interface.png){ width=100% }

# Research impact statement

This version provides verification evidence rather than evidence of research
use. Automated tests cover analytic isotropic limits, the
engineering shear convention, stability checks, crystal
templates, directional sampling, exports, rendering metadata, and GUI smoke
behaviour. A runnable synthetic example verifies a prescribed isotropic response
and writes a complete analysis package; the distribution is also installable
and buildable in a clean Python environment.

As of 12 August 2026, we have not identified a peer-reviewed publication,
preprint, independent research group, or established research pipeline using
AnisoScope. The paper therefore makes no claims about user numbers, performance
superiority, or scientific results enabled by the software. The project does not
yet satisfy JOSS's research-use screening criterion.

# AI usage disclosure

OpenAI Codex (GPT-5 and GPT-5.6 Terra; service build identifiers were not
exposed) assisted with repository auditing, documentation and test development,
manuscript editing, and preparation of JOSS submission materials.
The author reviewed, edited, and validated all AI-assisted outputs and made the
core design decisions.

# Acknowledgements

This work received no specific funding. The author declares no competing
interests, and there are no additional contributors to acknowledge.

# References
