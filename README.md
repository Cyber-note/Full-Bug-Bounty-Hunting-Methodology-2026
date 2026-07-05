# 🕵️‍♂️ Full Bug Bounty Hunting & Red Teamers Methodology 2026
Created by Cybernote, aspiring Red Team Operator and Bug Bounty Hunter. This repository documents my methodology, notes and workflow for web application security testing.

⭐ If you found this project useful Follow me on X for more Offensive Security research: { https://x.com/Cybernote9 } 

---

## Philosophy

Most hunters treat Recon as a checklist. I treat it as an **intelligence operation**.

The goal isn't to run every tool — it's to map the full attack surface faster and deeper than anyone else. Every phase feeds the next. Every finding is a pivot point.

This methodology is ordered by **signal-to-noise ratio**: start wide and passive, then narrow down aggressively before you ever send an exploit.

---

## 📌 Table of Contents

1. [Phase 1 — Passive Subdomain Enumeration](#phase-1--passive-subdomain-enumeration)
2. [Phase 2 — Active Subdomain Enumeration & Bruteforce](#phase-2--active-subdomain-enumeration--bruteforce)
3. [Phase 3 — Infrastructure Mapping (ASN / CIDR / IPs)](#phase-3--infrastructure-mapping-asn--cidr--ips)
4. [Phase 4 — WAF Bypass & Origin IP Discovery](#phase-4--waf-bypass--origin-ip-discovery)
5. [Phase 5 — Merge, Resolve & Alive Host Detection](#phase-5--merge-resolve--alive-host-detection)
6. [Phase 6 — Virtual Host Enumeration](#phase-6--virtual-host-enumeration)
7. [Phase 7 — URL & Endpoint Discovery](#phase-7--url--endpoint-discovery)
8. [Phase 8 — JavaScript Analysis & Secret Extraction](#phase-8--javascript-analysis--secret-extraction)
9. [Phase 9 — Directory & Sensitive File Discovery](#phase-9--directory--sensitive-file-discovery)
10. [Phase 10 — GitHub & Source Code Intelligence](#phase-10--github--source-code-intelligence)
11. [Phase 11 — Port Scanning & Service Fingerprinting](#phase-11--port-scanning--service-fingerprinting)
12. [Phase 12 — Automated Vulnerability Scanning](#phase-12--automated-vulnerability-scanning)
13. [Phase 13 — Subdomain Takeover Detection](#phase-13--subdomain-takeover-detection)
14. [Wordlists Reference](#wordlists-reference)
15. [OSINT Platforms Reference](#osint-platforms-reference)

---

## ⚙️ Prerequisites & Environment

Before executing the commands below, ensure your environment variables are properly exported:

```bash
export DNS_WORDLIST="/path/to/subdomains-wordlist.txt"
export WEB_WORDLIST="/path/to/directories-wordlist.txt"
export GITHUB_TOKEN="your_github_personal_access_token"
export PDCP_API_KEY="your_projectdiscovery_chaos_key"
```
---

## Phase 1 — Passive Subdomain Enumeration

> No traffic hits the target. Pure intelligence gathering from public sources.

### Core Tools

```bash
# subfinder — fast, API-powered passive enumeration
subfinder -d target.com -all -recursive -o subs_subfinder.txt

# assetfinder — finds related domains and subdomains
echo target.com | assetfinder -subs-only > subs_assetfinder.txt

# amass — deep OSINT engine
amass enum -d target.com -o subs_amass.txt
amass enum -d target.com -brute -w $DNS_WORDLIST -o subs_amass_brute.txt

# findomain — multi-source passive recon
findomain -t target.com -u subs_findomain.txt

# chaos — ProjectDiscovery's curated dataset (requires API key)
export PDCP_API_KEY=YOUR_KEY
chaos -d target.com -o subs_chaos.txt

# github-subdomains — mines developer code for hidden endpoints
github-subdomains -d target.com -t $GITHUB_TOKEN -o subs_github.txt
```

### Certificate Transparency (SSL)

One of the most underrated passive sources — every SSL cert issued is public record.

```bash
curl -s "https://crt.sh/?q=%25.target.com&output=json" \
  | jq -r '.[].name_value' \
  | sed 's/\*\.//g' \
  | tr ',' '\n' \
  | grep -oE "[A-Za-z0-9._-]+\.target\.com" \
  | sort -u > subs_crt.txt
```

### Aggregator (Run Everything at Once)

```bash
# subenum — wraps multiple tools in one shot
./subenum.sh -d target.com \
  -u wayback,crt,abuseipdb,Findomain,Subfinder,Amass,Assetfinder \
  -o subs_subenum.txt

# for a list of targets
./subenum.sh -l targets.txt \
  -u wayback,crt,abuseipdb,Findomain,Subfinder,Amass,Assetfinder \
  -o subs_subenum.txt
```

---

## Phase 2 — Active Subdomain Enumeration & Bruteforce

> Now we start touching the target — resolving domains and bruteforcing DNS.

### DNS Bruteforce

```bash
# puredns — high-speed DNS resolution with public resolvers
sudo wget -q https://raw.githubusercontent.com/trickest/resolvers/main/resolvers.txt
puredns bruteforce $DNS_WORDLIST target.com -r resolvers.txt -o subs_puredns.txt

# dnsx — lightweight DNS resolver with wildcard filtering
dnsx -silent -d target.com -w $DNS_WORDLIST -o subs_dnsx.txt

# dnscan — Python-based, useful for slower, stealthier scans
python dnscan.py -d target.com -w $DNS_WORDLIST -t 300 | tee subs_dnscan.txt
```

### Subdomain Permutation & Prediction

> Generate smart mutations based on already-discovered subdomains. Secret internal servers often follow predictable naming patterns.

```bash
# gotator — generates permutations from known subdomains
gotator -sub subs_all.txt -perm permutations.txt -depth 1 -numbers 3 -md | sort -u > subs_permuted.txt

# puredns resolves them
puredns resolve subs_permuted.txt -r resolvers.txt -o subs_permuted_alive.txt
```

### Subdomain Fuzzing with ffuf

```bash
# Standard subdomain fuzzing
ffuf -u https://FUZZ.target.com -w $DNS_WORDLIST -mc 200,301,302,403

# Hyphenated patterns (dev-target.com, api-target.com)
ffuf -u https://FUZZ-target.com -w $DNS_WORDLIST -mc 200,301,302,403

# Prefix patterns (www-old, www-beta, www-test)
ffuf -u https://FUZZwww.target.com -w $DNS_WORDLIST -mc 200,301,302,403
```

### Live Certificate Monitoring

> Catch new subdomains the moment they're issued — before the developer even secures them.

```bash
# gungnir — real-time certificate transparency monitoring
gungnir -d target.com
```

---

## Phase 3 — Infrastructure Mapping (ASN / CIDR / IPs)

> Most hunters stop at subdomains. This is where you go deeper — mapping the entire IP infrastructure of the organization.

### Step 1 — Find the ASN

```bash
# asnmap — resolves domain to ASN
asnmap -d target.com

# manual whois approach
dig target.com +short  # get an IP first
whois <IP> | grep -i "origin\|as\|route"

# spk — finds all ASNs for a company by name
spk -json -s "Tesla"
```

**Web alternatives:**
- https://bgp.he.net — search by company name
- https://bgp.tools — clean interface
- https://asnlookup.com — search by org name, ASN, or CIDR

### Step 2 — ASN to IP Ranges (CIDR)

```bash
# asnmap — direct CIDR extraction
asnmap -a AS33905 -silent

# whois-based approach — also extracts from routing databases
whois -h whois.radb.net -- '-i origin AS33905' \
  | grep -Eo "([0-9.]+){4}/[0-9]+" \
  | sort -u > cidr_ranges.txt

# Power move: resolve PTR records for every IP in a CIDR range
whois -h whois.radb.net -- '-i origin AS20461' \
  | grep -Eo "([0-9.]+){4}/[0-9]+" \
  | mapcidr -silent \
  | dnsx -ptr -resp-only -retry 3 -silent > ptr_domains.txt

# metabigor — pulls all IPs registered to an org from multiple sources
echo "Tesla" | metabigor net --org
echo "ASN33905" | metabigor net --asn
```

### Step 3 — CIDR to Individual IPs

```bash
# mapcidr — splits CIDR into individual IPs cleanly
echo 10.10.10.0/24 | mapcidr

# prips — generates full IP list for a range
prips 2.18.48.0/21 > ips_asn.txt
```

### Step 4 — Reverse DNS on IP Ranges

```bash
# dnsx PTR — resolves hostnames from IP blocks
echo 66.211.170.0/23 | dnsx -silent -resp-only -ptr

# hakrevdns — reverse DNS at scale
hakrevdns -d target.com -R resolvers.txt

# resolveDomains — check if subdomains resolve to live IPs
resolveDomains -d all_subs.txt > resolved.txt
awk '{print $3}' resolved.txt | sort -u > unique_ips.txt
```

### TLD Expansion

> A company that owns `target.com` often neglects `target.io`, `target.net`, `target.xyz` — completely separate attack surface with weaker defenses.

```bash
# tldbrute — discovers all registered TLD variants
tldbrute -d target.com

# Full IANA TLD list approach
wget -q https://data.iana.org/TLD/tlds-alpha-by-domain.txt
cat tlds-alpha-by-domain.txt \
  | tr '[:upper:]' '[:lower:]' \
  | while read t; do echo "target.$t"; done \
  | httpx -mc 200 > tlds_alive.txt

# Apply same logic across subdomain list
cat all_subs.txt | while read sub; do
  cat tlds-alpha-by-domain.txt \
    | tr '[:upper:]' '[:lower:]' \
    | sed "s/^/$sub./"
done | dnsx -silent > subs_tld_expanded.txt
```

---

## Phase 4 — WAF Bypass & Origin IP Discovery

> Cloudflare and similar WAFs protect 70%+ of bug bounty targets. Finding the origin IP exposes the raw server — no firewall, no rate limiting.

### Method 1 — Favicon Hash (Most Reliable)

Companies reuse the same favicon across all their infrastructure. The hash is a fingerprint you can search in Shodan.

```bash
# favUp — finds origin IP via favicon hash + Shodan
python3 favUp.py -ff favicon.ico --shodan-cli
python3 favUp.py --web target-behind-cloudflare.com -sc

# favirecon — lightweight favicon recon
favirecon -u https://target.com/ -v

# FavFreak — identifies unique favicon hashes across your subdomain list
# Anything with a different hash = different infrastructure = worth investigating
cat subs.txt | python3 favfreak.py
```

**Manual approach:**
1. Go to https://favicons.teamtailor-cdn.com/ → paste target URL → get the favicon
2. Go to https://favicon-hash.kmsec.uk/ → paste favicon URL → get the hash
3. Search Shodan: `http.favicon.hash:-382492124`

**If an IP returns your target's favicon but isn't a Cloudflare IP → that's your origin server.**

### Method 2 — Historical DNS Records

```bash
# originiphunter — queries multiple sources for historical IPs
echo "target.com" | originiphunter
cat domains.txt | originiphunter
```

**OSINT sources for historical IPs:**
- https://securitytrails.com — DNS history
- https://viewdns.info/reverseip/ — reverse IP lookup
- https://search.censys.io — search `parsed.names: target.com`
- https://www.shodan.io — search `ssl.cert.subject.cn:target.com`
- https://netlas.io — deep infrastructure search

### Method 3 — Google Analytics ID

> One Analytics ID can reveal an entire corporate family — subsidiaries, acquired companies, international domains.

```bash
# Discover ID and linked domains
cat subdomains.txt | analyticsrelationships

# Manual lookup
# https://builtwith.com/relationships/target.com
# https://api.hackertarget.com/analyticslookup/?q=target.com
# https://api.hackertarget.com/analyticslookup/?q=UA-16316580
```

---

## Phase 5 — Merge, Resolve & Alive Host Detection

> Every phase generates output files. Here we consolidate, deduplicate, and identify what's actually alive.

### Merge All Subdomain Sources

```bash
cat subs_*.txt ptr_domains.txt subs_permuted_alive.txt \
  | anew \
  | tee all_subs.txt

wc -l all_subs.txt
```

### Alive Host Detection with httpx

```bash
# Basic — just get alive hosts
cat all_subs.txt | httpx -silent -o alive_subs.txt

# Enriched — status codes, titles, web server, response size
cat all_subs.txt | httpx \
  -status-code -content-length -web-server -title \
  -follow-redirects -o alive_enriched.txt

# Filter by status — only 200s
cat all_subs.txt | httpx -status-code -follow-redirects -match-code 200

# Filter out noise — exclude 400s
cat all_subs.txt | httpx -status-code -follow-redirects -filter-code 400

# Response code logic
# 404 → try waybackurls + fuzzing
# 403 → try bypass techniques
```

### Visual Recon — Screenshot Everything

> You can't manually open 500 subdomains. Let the tool scan and screenshot — you browse the results and pick targets.

```bash
# gowitness — screenshots all alive hosts
gowitness file -f alive_subs.txt -P ./screenshots/ --no-http

# eyewitness — with reporting
python3 EyeWitness.py -f alive_subs.txt --web -d ./eyewitness_output
```

### CMS Detection

```bash
# whatweb — fingerprints CMS and technologies
whatweb -i alive_subs.txt -a 3 -t 50 --log-brief=cms_results.txt

# wappalyzer CLI — tech stack fingerprinting
wappalyzer https://target.com
```

---

## Phase 6 — Virtual Host Enumeration

> Some hosts only respond when you hit them with the correct `Host` header — they're invisible to normal scanners. VHOST enumeration exposes internal services mapped to IPs.

```bash
# Fuzz for internal virtual hosts on discovered IPs
ffuf -u http://<IP> \
  -w $DNS_WORDLIST \
  -H "Host: FUZZ.target.com" \
  -fs 0 \
  -mc 200,301,302,401,403

# HTTPS variant
ffuf -u https://target.com \
  -w $DNS_WORDLIST \
  -H "Host: FUZZ.target.com" \
  -mc 200,301,302,401,403
```

### Accessing VHOST Targets

```bash
# Method 1 — direct curl with Host header
curl -H "Host: dev.target.com" http://<IP>

# Method 2 — /etc/hosts injection (for browser access)
sudo nano /etc/hosts
# Add: 23.7.244.99  dev.target.com internal.target.com admin.target.com

# Then open in browser: http://dev.target.com
# Try OWASP Top 10: IDOR, Auth, Logic, API abuse
```

### IPs to Hostnames via SSL Certificates

```bash
# hosthunter — extracts hostnames from SSL certs on IP list
python3 hosthunter.py ips.txt

# httpx — check which IPs serve web content
cat ips.txt | httpx -ports 80,443,8080,8000,8888 -status-code -title
```

---

## Phase 7 — URL & Endpoint Discovery

> The goal here is to build an exhaustive map of every URL the application has ever exposed — past and present.

### Historical URL Collection

```bash
# waybackurls
cat alive_subs.txt | waybackurls > urls_wayback.txt

# waymore — smarter, filters by date and limits results
waymore -i alive_subs.txt -mode U -l 1000 -from 2021 -oU urls_waymore.txt

# gau — aggregates from multiple sources
cat alive_subs.txt | gau --threads 200 > urls_gau.txt

# gauplus — gau with improvements
gauplus -t 200 -random-agent < alive_subs.txt > urls_gauplus.txt
```

### Active Crawling

```bash
# katana — modern JS-aware crawler (best overall)
katana -u alive_subs.txt \
  -jc -kf all -d 5 \
  -headless -fx -aff \
  -fs rdn -f url -silent > urls_katana.txt

# gospider
gospider -S alive_subs.txt -t 20 -d 3 --js --sitemap --robots -o ./gospider_output/
gospider -S alive_subs.txt \
  | sed -n 's/.*\(https:\/\/[^ ]*\)]*.*/\1/p' >> urls_gospider.txt

# hakrawler
cat alive_subs.txt | hakrawler -subs -u -insecure > urls_hakrawler.txt
```

### Parameter Discovery

```bash
# paramspider — finds parameters from Wayback data
paramspider -d target.com -o urls_params.txt

# x8 — hidden parameter discovery via HTTP response comparison
x8 -u "https://target.com/endpoint" -o urls_x8.txt
```

### Merge All URLs

```bash
cat urls_wayback.txt urls_waymore.txt urls_gau.txt urls_gauplus.txt \
    urls_katana.txt urls_gospider.txt urls_hakrawler.txt urls_params.txt \
  | anew \
  | tee all_urls.txt

wc -l all_urls.txt
```

### Extract High-Value URL Categories

```bash
# JavaScript files
cat all_urls.txt | grep -iE '\.js(\?|$)' | grep -iv '\.json' | sort -u > js_urls.txt

# API endpoints
cat all_urls.txt | grep -Ei '\.(json|xml|graphql|gql)(\?|$)' > api_urls.txt

# Backend files (PHP, ASP, JSP)
cat all_urls.txt | grep -Ei '\.(php|asp|aspx|jsp|cfm|cgi)(\?|$)' > backend_urls.txt

# Login & auth flows
cat all_urls.txt | grep -Ei "login|signin|auth|oauth|reset|password" > auth_urls.txt

# File upload endpoints
cat all_urls.txt | grep -Ei "upload|file|download|image|media" > upload_urls.txt

# Admin panels
cat all_urls.txt | grep -Ei "admin|dashboard|internal|manage" > admin_urls.txt

# Sensitive file extensions
cat all_urls.txt | grep -Ei '\.(env|bak|config|sql|log)(\?|$)' > sensitive_urls.txt

# IDOR candidates (URLs with numeric IDs)
cat all_urls.txt | grep -Ei '[0-9]{2,}' > idor_candidates.txt

# Open redirect candidates
cat all_urls.txt | grep -Ei "redirect|callback|goto|return|dest=|r=|u=|url=" > redirect_urls.txt

# Cloud credential exposure
cat all_urls.txt | grep -Ei "aws|s3|bucket|gcp|azure|token|apikey|secret" > cloud_urls.txt

# Everything interesting in one shot
cat all_urls.txt | urinteresting
```

### Extract & Filter Parameters

```bash
# Extract all parameterized URLs
cat all_urls.txt | grep "=" | anew params.txt

# Prepare for fuzzing
cat all_urls.txt | grep "=" | qsreplace "FUZZ" | anew param_fuzz.txt

# Deduplicate by parameter name (remove value noise)
cat all_urls.txt | grep '=' | sed 's/=[^&]*/=/g' | sort -u > params_clean.txt

# Discover hidden parameters with arjun
arjun -i backend_urls.txt -o arjun_params.json
arjun -u https://target.com/endpoint -m POST
```

### Find Live URLs

```bash
cat all_urls.txt | httpx -status-code -content-length -silent > live_urls.txt
```

---

## Phase 8 — JavaScript Analysis & Secret Extraction

> JavaScript files are goldmines. They contain hardcoded API keys, internal endpoints, authentication logic, and sometimes full backend infrastructure maps.

### Extract Secrets from JS

```bash
# subjs — pulls JS files from a list of URLs
cat all_urls.txt | subjs | tee js_files.txt

# mantra — regex-based secret scanner for JS
cat js_urls.txt | mantra

# jsecret — finds sensitive patterns in JS files
cat js_urls.txt | jsecret

# jsleak — concurrent JS secret scanner
cat js_urls.txt | xargs -P 20 -I {} \
  jsleak -s -l -k -e {} >> jsleak_output.txt

# Quick regex scan on any JS file
grep -E "api[_-]?key|token|secret|password|bearer|client_id" target.js
```

### Source Map Exploitation

> When source maps are left enabled in production, you can recover the full pre-compiled source code.

```bash
# Find .map files via Wayback
curl -s "https://web.archive.org/cdx/search/cdx?url=*.target.com/*&collapse=urlkey&output=text&fl=original&filter=original:.*.js.map$"

# Download and extract
wget https://target.com/static/app.js.map
node -e "
const map = require('./app.js.map');
map.sources.forEach((src, i) => {
  require('fs').writeFileSync(src.split('/').pop(), map.sourcesContent[i]);
});
"
```

### TruffleHog — Deep Git History Scanning

```bash
# Scan a public GitHub repo (finds secrets even if deleted minutes later)
trufflehog git https://github.com/target/repo --results=verified

# Scan entire org
trufflehog github --org=target \
  --token=$GITHUB_TOKEN \
  --only-verified \
  --threads=20 \
  --json > trufflehog_target.json

# Scan local filesystem
trufflehog filesystem ./js_files/ --json > trufflehog_local.json
```

### Lazyegg

```bash
# Crawls and extracts links, APIs, IPs from JS files
python lazyegg.py https://target.com
python lazyegg.py https://target.com/js/auth.js

# Combine with waybackurls for deep coverage
waybackurls target.com \
  | grep '\.js$' \
  | awk -F '?' '{print $1}' \
  | sort -u \
  | xargs -I{} bash -c 'python lazyegg.py "{}" --js_urls --domains --ips' \
  > lazyegg_output.txt
```

---

## Phase 9 — Directory & Sensitive File Discovery

> Even fully patched applications leak sensitive data through forgotten files, backup archives, and misconfigured directories.

### dirsearch

```bash
# Full-featured directory scan
dirsearch -u https://target.com \
  -e php,asp,aspx,jsp,json,xml,txt,log,ini,cfg,conf,bak,old,backup,zip,tar,gz,rar,sql,swp,db \
  -t 80 -r -R 3 \
  --deep-recursive \
  --random-agent \
  --full-url \
  -i 200,204,301,302,307,308,401,403 \
  -x 404,500,502,503,504 \
  -o dirsearch_results.txt

# Scan all alive subdomains at once
dirsearch -l alive_subs.txt \
  --full-url \
  -e php,env,json,yaml,bak,zip,sql,conf \
  -o dirsearch_all.txt
```

### ffuf

```bash
# Standard directory fuzzing
ffuf -u https://target.com/FUZZ \
  -w $WEB_WORDLIST \
  -t 80 \
  -e .html,.php,.asp,.aspx,.js,.json,.xml,.config,.bak,.old,.zip,.rar \
  -mc 200,204,301,302,307,401,403 \
  -of json -o ffuf_dirs.json

# Recursive fuzzing
ffuf -u https://target.com/FUZZ \
  -w $WEB_WORDLIST \
  -recursion -recursion-depth 3 \
  -mc 200,204,301,302,307,401,403

# 403 Bypass — try alternate headers
ffuf -u https://target.com/admin \
  -w https://github.com/Karanxa/Bug-Bounty-Wordlists/raw/main/403_header_payloads.txt \
  -H "FUZZ" \
  -mc 200,301,302

# WAF bypass via IP header spoofing
ffuf -u https://target.com/FUZZ \
  -w $WEB_WORDLIST \
  -H "X-Forwarded-For: 127.0.0.1" \
  -H "X-Forwarded-Host: 127.0.0.1" \
  -H "X-Custom-IP-Authorization: 127.0.0.1" \
  -H "X-Original-URL: /FUZZ" \
  -mc 200,301,302,307,401

# Smart auto-calibration (defeats wildcard 200 responses)
ffuf -u https://target.com/FUZZ \
  -w $WEB_WORDLIST \
  -mc all -fc 404 -ac -sf -s
```

> **Key insight:** When a path responds with `/` as the last character, it means there's more to enumerate behind it. Always recurse.

### feroxbuster

```bash
feroxbuster -u https://target.com \
  -w $WEB_WORDLIST \
  -t 300 -k -d 3 \
  -x php,html,json,js,log,txt,bak,old,zip,tar,gz
```

### Wayback Sensitive File Mining

```bash
# The definitive sensitive file pattern — run on every target
waybackurls https://target.com \
  | grep -E "\.(xls|xlsx|csv|sql|db|bak|backup|old|tar\.gz|tgz|zip|7z|rar|pdf|pem|key|crt|env|json|yml|yaml|conf|config|git|htpasswd|log|dump|DS_Store)" \
  | sort -u > sensitive_wayback.txt
```

### Backup File Checker

```bash
# bfac — finds accidentally exposed backup files
bfac --url https://target.com \
  --detection-technique all \
  --level 3 \
  --exclude-status-codes 404,500
```

### GitHub Endpoints — Find Leaked API Paths

```bash
# github-endpoints — mines developer repos for internal paths
github-endpoints -q -k -d target.com -t $GITHUB_TOKEN

# Example find: var api_url = "https://dev-test.target.com/api/v1/debug"
```

### Robots.txt History

```bash
# roboxtractor — retrieves historical robots.txt to find hidden paths
cat alive_subs.txt | roboxtractor -m 1 -wb
```

### From 404 to Gold — Historical Page Recovery

```bash
# Step 1: Collect historical URLs
waybackurls https://target.com | grep "webstat" > old_pages.txt

# Step 2: Check Wayback Machine snapshots
# https://web.archive.org/web/*/https://target.com/webstat/*

# Step 3: Re-crawl for linked resources around that path
gospider -s https://target.com -a -r \
  | grep -oE 'https?://[^[:space:]"]+' \
  | grep "/webstat/"
```

### Google Sheets Leak Hunting

```bash
# Organizations accidentally expose internal sheets
site:*.target.com intext:"docs.google.com/spreadsheets"
site:docs.google.com/spreadsheets "target.com"
site:docs.google.com/spreadsheets "@target.com"
site:docs.google.com/spreadsheets "password" "target.com"
```

---

## Phase 10 — GitHub & Source Code Intelligence

> Developers accidentally push secrets constantly. This phase hunts for API keys, tokens, passwords, and internal infrastructure details across public repositories.

### GitDorker — Targeted GitHub Search

```bash
python3 GitDorker.py \
  -tf $GITHUB_TOKEN \
  -q target.com \
  -d dorks/medium_dorks.txt \
  -o gitdorker_results.txt

# Also search by employee names found in metadata
python3 GitDorker.py -tf $GITHUB_TOKEN -q "john.doe@target.com" -d dorks/medium_dorks.txt
```

**Dork resources:**
- https://github.com/Proviesec/github-dorks
- https://mr-koanti.github.io/github.html

### TruffleHog — Verified Secret Detection

```bash
# Scan org — finds secrets even in deleted commits
trufflehog github \
  --org=target \
  --token=$GITHUB_TOKEN \
  --only-verified \
  --threads=20 \
  --json > trufflehog_target.json

# Docker variant
docker run --rm -it trufflesecurity/trufflehog:latest \
  github --only-verified --org=target
```

### shhgit — Real-Time GitHub Monitoring

> Watch for secrets being pushed to GitHub **right now** — before the developer can delete them.

```bash
# Monitor globally for common secret patterns
shhgit --search-query \
  'path:*.env OR "DB_PASSWORD=" OR "AWS_ACCESS_KEY_ID=" OR "-----BEGIN RSA PRIVATE KEY-----"'

# Monitor a specific target org in real-time
shhgit --search-query \
  'target.com (path:*.env OR "DB_PASSWORD=" OR "api_key=")'
```

### git-wild-hunt — File Extension Search

```bash
# Find specific file types in a target's repos
python git-wild-hunt.py -s "org:Target extension:json filename:creds language:JSON"
python git-wild-hunt.py -s "org:Target extension:sql filename:backup"
python3 git-wild-hunt.py -s "target.com gitlab_token"
```

### GitLab — Private Infrastructure

> Large companies use internal GitLab instances instead of GitHub — this is where the real secrets live.

```bash
# Discover GitLab instance
# Try: gitlab.target.com | git.target.com | code.target.com

# Authenticate with a found token
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.target.com/api/v4/user"

# List accessible projects
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.target.com/api/v4/projects?membership=true&simple=true"

# Deep scan for secrets across all accessible repos
gitleaks detect \
  --source https://gitlab.target.com \
  --access-token $GITLAB_TOKEN -v
```

### Metadata Extraction

```bash
# metafinder — downloads public documents and extracts metadata
# Reveals: usernames, software versions, internal file paths, email patterns
metafinder -d "target.com" -l 10 -go -bi -ba -o metadata.txt

# Also try on subdomains
metafinder -d "dev.target.com" -l 10 -go -bi -ba -o metadata_dev.txt
```

**Why this matters:** A PDF's metadata might reveal `C:\Users\john.doe\Projects\InternalAPI\` — that's a username and project name you can use for further recon.

---

## Phase 11 — Port Scanning & Service Fingerprinting

> Web ports are expected. Non-standard ports are where misconfigured services, admin panels, and exposed APIs hide.

### Step 1 — Fast Port Scan (Top 1000)

```bash
# naabu — extremely fast Go-based port scanner
naabu -l unique_ips.txt \
  -exclude-ports 80,443 \
  -rate 2000 \
  -o open_ports.txt

# Against subdomain list directly
naabu -list alive_subs.txt -p - -rate 1000 -c 50 -o ports_full.txt
```

### Step 2 — Full Port Scan (65535)

```bash
naabu -l unique_ips.txt \
  -p - \
  -exclude-ports 80,443,8080,8000,8888 \
  -o ports_fullscan.txt
```

### Step 3 — Service Version Detection

```bash
# nmap — version + default script scan on discovered open ports
nmap -sV -sC -iL open_ports.txt -oN nmap_versions.txt

# Combine naabu + nmap in one pipeline
naabu -list unique_ips.txt -p - -rate 1000 -c 50 \
  -nmap-cli 'nmap -sV -sC' \
  -o ports_with_services.txt
```

### Step 4 — Vulnerability Scan on Services

```bash
# nuclei — scan network-layer vulnerabilities
nuclei -l unique_ips.txt \
  -t nuclei-templates/network/ \
  -H "X-Forwarded-For: 127.0.0.1" \
  -mhe 4 -rl 30 -es info

# Nessus (GUI) — if available, give it the full CIDR range
# Feed: 2.18.48.0/21
# Let it scan for CVEs, misconfigurations, and credential issues
```

---

## Phase 12 — Automated Vulnerability Scanning

### nuclei — CVE & Misconfiguration Detection

```bash
# Scan all alive subdomains for known CVEs + exposures
nuclei -l alive_subs.txt \
  -t nuclei-templates/http/ \
  -severity critical,high,medium \
  -H "X-Forwarded-For: 127.0.0.1" \
  -H "X-Forwarded: 127.0.0.1" \
  -mhe 4 -rl 30 -es info \
  -o nuclei_results.txt

# Target exposure templates specifically
nuclei -l alive_subs.txt \
  -t nuclei-templates/http/exposures/ \
  -o nuclei_exposures.txt

# Tor proxy — rotates IP every request, defeats all rate limiting
nuclei -u https://target.com \
  -p socks5://127.0.0.1:9050
```

### SQL Injection

```bash
# sqlmap on parameterized URLs
sqlmap -u "https://target.com/page.php?id=1" \
  --dbs --banner --batch --random-agent

# From saved request file (Burp export)
sqlmap -r request.txt --dbs --banner --batch --random-agent
```

### Subdomain Takeover Check

See [Phase 13](#phase-13--subdomain-takeover-detection).

### API Key Validation Pipeline

```bash
# Find API keys in JS/JSON/config files, then verify them
echo "https://target.com" \
  | gau \
  | grep -E '\.js$|\.json$|\.xml$|\.env$|\.config$' \
  | httpx -silent -mc 200 \
  | parallel -j 50 "curl -s {} \
    | grep -oP '(?:api[_-]?key|secret|token)[\"'\''']?\s*[:=]\s*[\"'\''']?([A-Za-z0-9_\-]{20,})' \
    | tee -a api_keys.txt"
```

---

## Phase 13 — Subdomain Takeover Detection

> A subdomain pointing to a deregistered third-party service (Heroku, S3, Zendesk, etc.) can be claimed by anyone. Worth thousands of dollars when found.

```bash
# subzy — fast takeover scanner
subzy run --targets all_subs.txt --hide_fails --vuln \
  | grep -v -E "Akamai|available|\-"

# dnsx — get CNAME records for all subdomains
dnsx -retry 3 -a -aaaa -cname -ns -ptr -mx -soa \
  -resp -silent \
  -l all_subs.txt \
  | tee dns_records.txt
```

**What to look for:**

```
api.target.com [CNAME] clusters.heroku.com     ← check if registered
help.target.com [CNAME] target.zendesk.com     ← check if available
cdn.target.com [CNAME] storage.s3.amazonaws.com ← check bucket name
```

### Verify Takeover Candidates

```bash
# Dig into the suspect subdomain
dig help.target.com CNAME

# Check the Google Dig Tool
# https://toolbox.googleapps.com/apps/dig/#TXT/

# If there's no TXT record → the subdomain is up for grabs
```

### S3 Takeover Pipeline

```bash
subfinder -d target.com -silent \
  | dnsx -silent -cname \
  | grep "s3.amazonaws" \
  | httpx -mc 404 \
  | while read sub; do
      aws s3 mb "s3://${sub#https://}" && echo "CLAIMED: $sub"
    done
```

---

## Wordlists Reference

| Purpose | Path |
|---|---|
| DNS — Top 100K | `/usr/share/wordlists/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt` |
| DNS — Jhaddix | `/usr/share/wordlists/seclists/Discovery/DNS/dns-Jhaddix.txt` |
| DNS — Top 1M | `/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-110000.txt` |
| DNS — CommonSpeak2 | `/usr/share/wordlists/commonspeak2-wordlists-master/subdomains/subdomains.txt` |
| DNS — Best | `sudo wget https://wordlists-cdn.assetnote.io/data/manual/best-dns-wordlist.txt` |
| Web — Large Dirs | `/usr/share/wordlists/seclists/Discovery/Web-Content/raft-large-directories.txt` |
| Web — Large Files | `/usr/share/wordlists/seclists/Discovery/Web-Content/raft-large-files.txt` |
| Web — Common | `/usr/share/wordlists/seclists/Discovery/Web-Content/common.txt` |
| Web — Medium | `/usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt` |
| Parameters | `/usr/share/wordlists/seclists/Discovery/Web-Content/burp-parameter-names.txt` |

---

## OSINT Platforms Reference

| Platform | Primary Use |
|---|---|
| https://securitytrails.com | DNS history, subdomain data |
| https://shrewdeye.app | Fast passive subdomain finder |
| https://netlas.io | Deep infrastructure search |
| https://urlscan.io | URL and page analysis |
| https://search.censys.io | Internet-wide host scanning |
| https://www.shodan.io | IoT and service discovery |
| https://otx.alienvault.com | Threat intelligence |
| https://crt.sh | Certificate transparency logs |
| https://bgp.he.net | ASN and BGP routing data |
| https://search.dnslytics.com/cidr | CIDR-based domain lookup |
| https://viewdns.info | Reverse IP and DNS history |
| https://www.virustotal.com | Multi-source domain intel |
| https://builtwith.com | Tech stack and GA ID lookup |
| https://api.hackertarget.com | Analytics relationship mapping |
| https://asnlookup.com | ASN search by org name |
| https://bgp.tools | Modern BGP/ASN explorer |
| https://subdomainfinder.c99.nl | Quick subdomain lookup |
| https://www.favihash.com | Manual favicon hash generator |

---

*Methodology built from real engagements. Every command here has been run against live targets.* 
### 📄 License

Licensed under the MIT License. Created & Maintained by **Cybernote** © 2026.
