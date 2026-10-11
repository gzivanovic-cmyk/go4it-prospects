#!/usr/bin/env bash
# GO 4IT Prospects sync (alleen GO 4IT-Studio-data; nooit AIS of It's Just Software)
# Werkwijze voor GO 4IT Webbeheer (enige bot die pusht), dagelijks 07:45:
#  1. Haal met de Notion-connector (namespace user-Notion) ALLE rijen op uit
#     collection://443157c2-5283-451f-b928-33007b014b59 (notion-query-data-sources:
#     SELECT * FROM "collection://443157c2-5283-451f-b928-33007b014b59", pagineren bij has_more).
#     Is query-data-sources niet beschikbaar: notion-search in die data source + notion-fetch per pagina (<properties>).
#  2. Schrijf het resultaat ({"results":[...]} met per rij ook "url") naar private/prospects.json (gitignored).
#  3. ./sync.sh  -> logo's + screenshots (cache, >14 dagen verversen), versleutelen naar data/prospects.enc, pushen.
# Plaintext, screenshots en .password worden NOOIT gecommit.
set -euo pipefail
cd "$(dirname "$0")"
[ -f private/prospects.json ] || { echo "private/prospects.json ontbreekt"; exit 1; }
[ -f .password ] || { echo ".password ontbreekt"; exit 1; }
python3 fetch_logos.py || echo "Logo-ophalen mislukt, ga door"
python3 screenshots.py || echo "Screenshots mislukt, ga door"
node encrypt.js private/prospects.json data/prospects.enc .password
git add -A
if git ls-files | grep -Eq '^(private/|shots/|\.password)'; then echo "FOUT: geheime bestanden gestaged"; exit 1; fi
git diff --cached --quiet && { echo "Geen wijzigingen"; exit 0; }
git commit -qm "Sync prospects $(date '+%Y-%m-%d %H:%M')"
git push -q origin HEAD:main
echo "Gepusht. Live: https://gzivanovic-cmyk.github.io/go4it-prospects/"
