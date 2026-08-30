# Changelog

## [0.5.0](https://github.com/georgyturevich/ai-for-developers-project-386/compare/cal-bookings-api-v0.4.0...cal-bookings-api-v0.5.0) (2026-08-27)


### Features

* review hardening — strict contract scalars, fixed 30-minute Slot Grid, request limits, S5 conflict e2e ([#37](https://github.com/georgyturevich/ai-for-developers-project-386/issues/37)) ([d481fd9](https://github.com/georgyturevich/ai-for-developers-project-386/commit/d481fd97371815735ea5db03175de8ae5521f5e2))

## [0.4.0](https://github.com/georgyturevich/ai-for-developers-project-386/compare/cal-bookings-api-v0.3.1...cal-bookings-api-v0.4.0) (2026-08-12)


### Features

* **frontend:** add copyright footer label ([117d677](https://github.com/georgyturevich/ai-for-developers-project-386/commit/117d67740601a681f237aefd84292674d4f9592e))

## [0.3.1](https://github.com/georgyturevich/ai-for-developers-project-386/compare/cal-bookings-api-v0.3.0...cal-bookings-api-v0.3.1) (2026-08-12)


### Bug Fixes

* **ci:** chain Railway deploy into release-please.yml instead of a dead separate workflow ([#26](https://github.com/georgyturevich/ai-for-developers-project-386/issues/26)) ([bb8321c](https://github.com/georgyturevich/ai-for-developers-project-386/commit/bb8321cd8f14e0802735e3af953a03ecd6ad37ba))

## [0.3.0](https://github.com/georgyturevich/ai-for-developers-project-386/compare/cal-bookings-api-v0.2.0...cal-bookings-api-v0.3.0) (2026-08-12)


### Features

* Docker & Railway deployment — single-container image on $PORT ([#24](https://github.com/georgyturevich/ai-for-developers-project-386/issues/24)) ([3ef5366](https://github.com/georgyturevich/ai-for-developers-project-386/commit/3ef53669635680ce26e7f75feba48caec2edf385))

## [0.2.0](https://github.com/georgyturevich/ai-for-developers-project-386/compare/cal-bookings-api-v0.1.0...cal-bookings-api-v0.2.0) (2026-08-12)


### Features

* **ci:** automate releases with release-please ([c8a5780](https://github.com/georgyturevich/ai-for-developers-project-386/commit/c8a5780a1a2ee2f6434acc0b9773ccc23f492aaf))
* **ci:** run backend, frontend and e2e checks on push and pull requests ([1ebfd61](https://github.com/georgyturevich/ai-for-developers-project-386/commit/1ebfd61e7a11aa67f8630ce870b779087a7407c7))
* **test:** add Playwright e2e suite covering scenarios S1-S4 ([9e6bd9d](https://github.com/georgyturevich/ai-for-developers-project-386/commit/9e6bd9df8b00e9adde2abf97bb5e5f665dd66074))


### Bug Fixes

* **backend:** keep contract conformance independent of wall-clock time ([ba8d76a](https://github.com/georgyturevich/ai-for-developers-project-386/commit/ba8d76a193a7ef87705bb08c62251df3242f24e5))
* **backend:** pin the guest payload in the contract conformance suite ([25495e9](https://github.com/georgyturevich/ai-for-developers-project-386/commit/25495e907750a24f22e8e3bfc7e03fa458f62983))
* **ci:** keep release-please on the 0.x line and fix PR-creation permission ([f5aa04f](https://github.com/georgyturevich/ai-for-developers-project-386/commit/f5aa04f3684938810e76a6e17373dd650a56aa65))
