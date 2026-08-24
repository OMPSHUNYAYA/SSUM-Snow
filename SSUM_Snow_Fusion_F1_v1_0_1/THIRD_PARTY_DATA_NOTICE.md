# Third-Party Data Notice

## NOAA / National Weather Service / National Centers for Environmental Information

The verification pipeline uses historical information obtained from NOAA / National Weather Service / National Centers for Environmental Information servers, including National Blend of Models station guidance and GHCN-Daily observations.

The National Weather Service states that information on government servers is in the public domain unless specifically annotated otherwise and may be used freely, subject to restrictions including no false claim of ownership, no implication of NOAA/NWS endorsement or affiliation, and no presentation of modified material as official government material.

NWS disclaimer:

`https://www.weather.gov/disclaimer/`

NCEI archive and data-licensing information:

`https://www.ncei.noaa.gov/archive`

NBM archive source used by the verification software:

`https://noaa-nbm-grib2-pds.s3.amazonaws.com/`

GHCN-Daily source used by the verification software:

`https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/`

The package does not claim ownership of NOAA, NWS, NCEP, NBM, NCEI, GHCN-Daily, source data, names, marks, products, or archives and does not imply endorsement.

NCEI holdings may include material contributed by non-federal sources. Users should review applicable dataset metadata and terms for any reuse beyond the source-access and verification activity described here.

## Redistribution design

Raw source payloads and acquisition caches are not distributed in this package. The package supplies source locators, deterministic acquisition and parsing software, frozen protocols, compact derived results, and cryptographic evidence identities.
