# Cross-Platform v4 Packaging and Release Plan

## Goal

Define a native-feeling release path for each target platform without fragmenting the codebase.

## Windows

Current status: existing baseline

Tasks:

- preserve the current release path as the regression baseline
- document current packaging inputs and outputs
- record runtime prerequisites

## macOS

Tasks:

- decide bundle strategy
- document signing requirements
- document notarization requirements
- document BLE, serial, and filesystem permission expectations
- define user install/update flow

## Linux Desktop

Tasks:

- choose preferred packaging format
- define dependency expectations
- document BLE and serial permission requirements
- define user install/update flow

## Raspberry Pi

Tasks:

- decide whether the deliverable is desktop app, packaged install, or managed deployment
- document system package prerequisites
- document device access permissions
- document expected display/runtime model
- define update path

## Release Checklist Template

- build artifact produced
- app launches
- profile path resolves correctly
- optional dependency fallback works
- release notes updated
- platform-specific prerequisites documented
