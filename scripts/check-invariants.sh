#!/usr/bin/env bash
# Fortunate Excavator — repository invariants.
#
# Mechanical checks for the rules in docs/build-guide.md that must never
# regress. Each is true today, so this starts green; a red run means a rule was
# broken, not that the check is flaky. Run locally or in CI:
#
#     scripts/check-invariants.sh
#
# Requires an `upstream` remote (or UPSTREAM_REF) for the zero-diff check.
#
# GPL-3.0-or-later, like the rest of this repository.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

fail=0
pass() { printf '  ok    %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=1; }

echo "Invariant 1 — upstream crates are unmodified (build-guide §9)"
UPSTREAM_REF="${UPSTREAM_REF:-upstream/develop}"
if ! git rev-parse --verify --quiet "$UPSTREAM_REF" >/dev/null; then
    bad "no ref '$UPSTREAM_REF' — add the upstream remote and fetch it (see NOTICE.md)"
else
    base="$(git merge-base HEAD "$UPSTREAM_REF")"
    changed="$(git diff --name-only "$base" HEAD -- imessage-database imessage-exporter)"
    if [ -z "$changed" ]; then
        pass "imessage-database/ and imessage-exporter/ match upstream at ${base:0:12}"
    else
        bad "upstream crates differ from ${base:0:12}; parser fixes go upstream first:"
        printf '        %s\n' $changed
    fi
fi

echo "Invariant 2 — LICENSE is upstream's, byte for byte (NOTICE.md)"
want=3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986
if command -v sha256sum >/dev/null; then got="$(sha256sum LICENSE | cut -d' ' -f1)"
else got="$(shasum -a 256 LICENSE | cut -d' ' -f1)"; fi
[ "$got" = "$want" ] && pass "LICENSE sha256 matches" || bad "LICENSE sha256 is $got, expected $want"

echo "Invariant 3 — no network code, ever (build-guide §6)"
# Crates whose purpose is talking to a network. Any of them in the lockfile is
# a violation, whatever feature or crate pulled it in.
denied='reqwest|hyper|hyper-util|ureq|curl|curl-sys|isahc|surf|attohttpc|h2|h3|quinn|tungstenite|tokio-tungstenite|rustls|native-tls|openssl|openssl-sys|tokio|async-std|mio|socket2|trust-dns-resolver|hickory-resolver|sentry|opentelemetry'
hits="$(grep -E "^name = \"($denied)\"$" Cargo.lock || true)"
[ -z "$hits" ] && pass "Cargo.lock contains no networking crates" \
    || { bad "networking crates in Cargo.lock:"; printf '        %s\n' "$hits"; }
src="$(grep -rnE 'std::net|TcpStream|TcpListener|UdpSocket|ToSocketAddrs' \
        --include='*.rs' . --exclude-dir=target || true)"
[ -z "$src" ] && pass "no std::net usage in any .rs file" \
    || { bad "socket APIs in source:"; printf '        %s\n' "$src"; }

echo
if [ "$fail" -ne 0 ]; then echo "Invariants: FAILED"; exit 1; fi
echo "Invariants: all hold"
