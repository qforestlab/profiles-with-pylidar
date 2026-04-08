# Manual for running pylidar
This is a manual for making vegetation profiles from RIEGL terrestrial laser scanning (TLS) data by running the [pylidar-tls-canopy](https://github.com/qforestlab/pylidar-tls-canopy) code.

# What are pylidar and pylidar-tls-canopy
**Pylidar** is set of Python modules which makes it easy to write lidar processing code in Python. Find more information [here](https://www.pylidar.org/en/latest/#introduction). 

**Pylidar-tls-canopy** is a subset of the larger pylidar project which focuses on processing TLS data from the RIEGL TLS scanners and the LEAF in-situ scanner.
The package is mainly used to extract gap-fraction-based estimation of plant area index and plant area volume density. The study mentioned below provides the theoretical basis for the calculations implemented in this package. The pylidar-tls-canopy package is well documented with a series of notebooks containing example implementations that can be found at the GitHub repository. 

> This guide helps to install pylidar-tls-canopy and calculate vegetation profiles.

# Steps

Follow the following steps to go from RIEGL VZ-series scans to vegetation profiles:

**1. [Installation](1_installation.md)**<br>
**2. [Data preparation](2_data-preparation.md)**<br>
**3. [Making profiles](3_making-profiles.md)**<br>
**4. [Averaging profiles - *coming soon*](4_averaging-profiles.md)**<br>
**5. [Extracting metrics - *coming soon*](5_extracting-metrics.md)**<br>

# Literature pylidar

Pylidar-tls-canopy is based on this paper:

[Estimating forest LAI profiles and structural parameters using a ground-based laser called ‘Echidna'](https://academic.oup.com/treephys/article-abstract/29/2/171/1642428)

Other papers that have used profiles from pylidar:

* [Implications of sensor configuration and topography on vertical plant profiles derived from terrestrial LiDAR](https://www.sciencedirect.com/science/article/pii/S0168192314000902)
* [Monitoring spring phenology with high temporal resolution terrestrial LiDAR measurements](https://www.sciencedirect.com/science/article/pii/S0168192315000106)
* [Variability and bias in active and passive ground-based measurements of effective plant, wood and leaf area index](https://www.sciencedirect.com/science/article/pii/S0168192318300297)


