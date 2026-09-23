#!/usr/bin/env bash
# Run this repository's full CI locally, exactly as GitHub Actions does.
#
#     scripts/ci-local.sh
#
# TZ is pinned because upstream's HTML/TXT exporter tests assert rendered
# timestamps in America/Los_Angeles; outside that zone ~60 of them fail for
# reasons that have nothing to do with the change under test.
#
# GPL-3.0-or-later, like the rest of this repository.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export TZ=America/Los_Angeles
export CARGO_TERM_COLOR="${CARGO_TERM_COLOR:-always}"

step() { printf '\n==> %s\n' "$*"; }

step "invariants";  scripts/check-invariants.sh
step "clippy";      cargo clippy --workspace --all-targets -- -D warnings
step "doc";         RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --workspace
step "test";        cargo test --workspace
step "release build"; cargo build --release

printf '\nCI: green\n'
