# GlowTact Website Scientific Constraints

## Mechanism
1. A black elastomer membrane lies over a microtextured clear gel.
2. The membrane is unbonded to the textured interface.
3. Microscopic air gaps remain in the unloaded state.
4. The unloaded interface appears gray due to diffuse reflection at the gel–air interface.
5. Pressure increases membrane–gel optical coupling.
6. The contacted region darkens because reflected light decreases and the black membrane absorbs light.
7. Greater pressure generally increases coupling and local darkening.
8. The contact area may expand with pressure.
9. Illumination is single-color and nondirectional.
10. Do not depict GlowTact as RGB photometric stereo.

## Terminology
Preferred:
- pressure-responsive signal
- pressure-induced optical coupling
- direct optical response to interfacial contact
- local darkening

Use caution with:
- direct pressure measurement
- calibrated pressure map
- pixel-wise pressure

Do not claim each pixel is calibrated pressure unless an explicit calibration is supplied.

## Optical Interpretation
The mechanism is related to frustrated internal reflection, but:
- most reflection may be partial rather than ideal total internal reflection
- reflection is described as diffuse
- schematic rays are not a quantitative optical model

## Interactive Demo
- conceptual, not FEA
- conceptual, not ray tracing
- no invented force units
- no membrane penetration
- visible air gap at zero pressure
- monotonic darkening with pressure
- synthetic tactile output labeled as simulated

Mandatory note:
> Conceptual visualization. Geometry and optical paths are schematic and are not a calibrated mechanical or ray-tracing simulation.

## Experimental Data
- use final source data only
- preserve units and log axes
- keep SNR threshold at 3 where used
- distinguish passive-object demonstrations from controlled threshold tests
- do not describe passive placement as a calibrated minimum-force measurement
- do not invent uncertainty
- do not smooth curves in a way that changes results

## GelSight Mini
Allowed:
- representative geometry-based VBTS baseline
- same controlled apparatus and acquisition protocol
- weaker response under the tested passive contacts
- lower low-force SNR if supported by source data

Avoid:
- GelSight cannot detect contact
- GelSight is generally insensitive
- GelSight always performs worse
- all GelSight systems require heavy computation

## 9DTact
- qualitative context only unless matched data exist
- state that implementations and object sets differ
- do not claim a controlled quantitative comparison

## Geometry
Allowed:
- useful spatial contact information
- qualitative reconstruction
- M1 threads with 0.25 mm pitch

Avoid:
- universal superiority
- exact height recovery without quantitative validation

## Force Estimation
Allowed:
- learned normal-force estimation
- identical architecture for both sensors
- held-out spatial locations
- low-force improvement if supported

Avoid:
- direct force measurement by the camera
- shear-force estimation unless results are included

## Scalability and Durability
Treat as implications unless validated.

Allowed:
- simple optical design
- compact fingertip form factors
- replaceable membrane as an engineering direction

Avoid:
- proven scalable
- proven more durable without lifetime testing
- maintenance-free
- indestructible membrane

## Publication
- preserve anonymity while required
- do not expose private affiliations
- disable unavailable links
- do not invent venue status or citation information
