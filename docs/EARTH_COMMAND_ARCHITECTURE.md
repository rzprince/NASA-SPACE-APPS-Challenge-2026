# BoponX Earth Command Architecture

## Design rule

Every dataset must have exactly one clear role in the decision pipeline.

The application should never show the same raw fact in several unrelated cards simply to fill the interface.

## Pipeline

    Global Field
        |
        v
    Earth Twin
        |
        +--> GPM IMERG spatial precipitation
        +--> SMAP spatial surface soil moisture
        +--> NASA GIBS true color context
        +--> NASA POWER recent agroclimate
        +--> NASA POWER climatology
        |
        v
    NASA Fusion Engine
        |
        +--> recent rainfall context
        +--> rainfall anomaly against historical month
        +--> recent temperature context
        +--> temperature shift against historical month
        +--> humidity and wind context
        |
        v
    Local Data Mesh
        |
        +--> verified country government adapter
        +--> FAO crop calendar fallback
        +--> farmer observations
        +--> real soil test only when available
        |
        v
    Rotation Lab
        |
        +--> farmer intention
        +--> crop history
        +--> water and drainage constraints
        +--> local calendar evidence
        +--> Earth Pulse context
        |
        v
    Decision Engine
        |
        +--> readiness / evidence gaps
        +--> immediate next action
        +--> three month location aware plan
        +--> exploration paths
        |
        v
    Farmer Action Card

## Scientific separation

### Direct Earth observation or satellite derived spatial evidence

- GPM IMERG precipitation
- SMAP surface soil moisture
- GIBS imagery delivery

### Analysis ready agroclimate context

- NASA POWER Daily

### Historical climate reference

- NASA POWER Climatology

### Local agricultural evidence

- national or local public sector source adapters
- FAO Crop Calendar fallback
- farmer supplied field observations
- soil test report when available

### Deterministic decision logic

No generative model performs climate calculations or invents agronomic thresholds.

## Why the local source layer is adapter based

There is no trustworthy universal endpoint for every local agriculture ministry in the world.

BoponX therefore treats global NASA coverage and local agricultural evidence as two separate layers.

A country adapter is only enabled after the source is verified.

This prevents a visually complete but scientifically false world map.
