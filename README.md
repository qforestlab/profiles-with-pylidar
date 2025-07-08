# Manual for running pylidar
This is a manual for making vegetation profiles from RIEGL terrestrial laser scanning (TLS) data by running the [pylidar-tls-canopy](https://github.com/armstonj/pylidar-tls-canopy) code.

# What are pylidar and pylidar-tls-canopy
Pylidar is set of Python modules which makes it easy to write lidar processing code in Python. Find more information [here](https://www.pylidar.org/en/latest/#introduction). Pylidat-tls-canopy is a subset of the larger pylidar project which focuses on processing TLS data from the RIEGL TLS scanners and the LEAF in-situ scanner.
The package is mainly used to extract gap-fraction-based estimation of plant area index and plant area volume density. The study mentioned below provides the theoretical basis for the calculations implemented in this package. 

The package is well documented with a series of notebooks containing example implementations that can be found at the github repository. 

# Steps

**1. [Installation](1_installation.md)**<br>
**2. [Data preparation](2_data-preparation.md)**<br>
**3. [Making profiles](3_making-profiles.md)**<br>
**4. [Averaging profiles](4_averaging-profiles.md)**<br>
**5. [Extracting metrics](5_extracting-metrics.md)**<br>

# Literature pylidar

Pylidar-tls-canopy is based on this paper:

[Estimating forest LAI profiles and structural parameters using a ground-based laser called ‘Echidna'](https://academic.oup.com/treephys/article-abstract/29/2/171/1642428)

Other papers that have used profiles from pylidar:

*insert links to papers*
