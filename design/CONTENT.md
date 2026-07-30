# GlowTact Website Content

## Title
**GlowTact: Simple and Compact Vision-Based Tactile Sensing with High Sensitivity and Spatial Resolution**

## Hero Subtitle
A pressure-responsive camera-based tactile sensing mechanism for compact humanoid fingertips.

## Short Summary
GlowTact converts optical coupling between a black elastomer membrane and a microtextured transparent gel into a direct high-contrast tactile image. It requires single-color, nondirectional illumination while preserving high sensitivity and fine spatial detail.

## Key Results
- gram-scale passive-contact detection
- normal-force estimation
- reconstruction of fine contact geometry, including M1 screw threads

## Mechanism Copy

### No Contact
Microscopic air gaps remain between the black membrane and the microtextured gel. Light is diffusely reflected at the gel–air interface, producing a light-gray tactile image.

### Contact
Pressure presses the membrane into optical contact with the textured gel. The reflective interface is reduced locally, and light is absorbed by the black membrane.

### Increasing Pressure
A larger fraction of the interface becomes optically coupled. The contact region becomes larger and darker.

## Conventional VBTS Comparison
> Many vision-based tactile sensors encode deformation through shading, marker displacement, depth imaging, or light attenuation. GlowTact instead produces optical contrast through pressure-induced coupling at the membrane–gel interface.

## Sensor Implementations

### Flat GlowTact
- textured XP-565 silicone
- black nitrile membrane
- acrylic backing and light guide
- single-color perimeter LEDs
- fisheye camera

### Omnidirectional Fingertip
- textured silicone over a clear epoxy skeleton
- black nitrile membrane
- LED ring
- fisheye camera

### Humanoid Fingertip
- approximately 17 mm wide
- front-facing tactile coverage
- wide-angle camera
- U-shaped LED strip
- curved gel body
- black nitrile membrane

## Lightweight Objects
Suggested headline:
**Visible passive contact under millinewton-scale loading**

Objects:
- M&M: approximately 1.0 g / 9.8 mN
- M6 nut: approximately 2.0 g / 20.0 mN
- M5×6 screw: approximately 2.4 g / 23.5 mN

Suggested text:
> The objects are placed on each sensor under gravity alone, without additional loading. GlowTact produces clearer spatially localized responses under the tested passive contacts.

## Sensitivity
Suggested headline:
**Strong low-force response across ten probe geometries**

Dataset summary:
- ten probe geometries
- 0–20 N
- 13,116 matched controlled-probing samples per sensor
- SNR threshold: 3

Use exact source data for every interactive chart.

## Geometry
Suggested headline:
**Fine contact geometry down to M1 threads**

Examples:
- Phillips screw
- M3
- M2.5
- M2
- M1.5
- M1
- ball array

Suggested text:
> Although GlowTact is based on pressure-induced optical coupling rather than photometric stereo, its images preserve sufficient spatial structure for contact-shape reconstruction.

If 9DTact is shown:
> Representative prior results are included only for qualitative context; implementations and object sets differ.

## Force Estimation
Suggested headline:
**Pressure-responsive images support continuous normal-force estimation**

Method summary:
- separate ImageNet-pretrained ResNet-18 regressors
- matched sensor datasets
- held-out spatial locations
- all depths from one indentation location remain in one split

Data:
- 13,116 controlled-probe frames
- 1,600 everyday-object frames
- 14,716 total frames per sensor
- objects: balloon, light bulb, pipe, rope

## Website Abstract
> Vision-based tactile sensors provide dense contact information for manipulation, but many designs are difficult to simplify for compact humanoid fingertips. GlowTact uses a microtextured transparent gel and an unbonded black elastomer membrane. Pressure increases optical coupling at the interface, creating a dark tactile response. The resulting architecture uses single-color, nondirectional illumination and supports passive-contact detection, normal-force estimation, and fine contact-geometry reconstruction in flat and fingertip form factors.

## Temporary Citation
Keep authors anonymous until public release.

```bibtex
@article{anonymous2026glowtact,
  title={GlowTact: Simple and Compact Vision-Based Tactile Sensing with High Sensitivity and Spatial Resolution},
  author={Anonymous},
  year={2026}
}
```
