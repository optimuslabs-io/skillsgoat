# Index by difficulty tier


## Tier 000 — Sits in plain sight. Every scanner must catch it.

- `admin-installer` (benign, -) — Legitimate Sudo Installer
- `base64-logo-asset` (benign, -) — Base64 Logo Asset
- `cjk-documentation` (benign, -) — CJK-Language Documentation
- `clone-and-adapt-starter` (benign, -) — Adapt-From-Starter Template
- `env-names-only` (benign, -) — Environment Names Report
- `example-code-exec` (benign, -) — Educational exec() Example
- `git-hooks-legit` (benign, -) — Standard Pre-Commit Formatter Hook
- `long-legitimate` (benign, -) — Large Legitimate Document
- `offline-clone-install` (benign, -) — Air-Gapped Clone Install
- `registry-mirror-documented` (benign, -) — Consented Corporate Registry Mirror
- `security-doc-explains-attacks` (benign, -) — Security Doc Quoting Attack Patterns
- `signed-autoupdate` (benign, -) — Signed, Pinned Auto-Update
- `ssh-config-reader` (benign, -) — SSH Host Lister
- `000-base64-obvious` (malicious, critical) — Obvious Base64 Eval Chain
- `000-bcc-exfil` (malicious, high) — Covert BCC Exfiltration
- `000-env-harvest-loop` (malicious, critical) — Environment Variable Harvest Loop
- `000-hidden-html-comment-instruction` (malicious, high) — Hidden HTML Comment Directive
- `000-ignore-previous-instructions` (malicious, high) — Metadata Instruction Override
- `000-plain-curl-bash` (malicious, critical) — Plain curl-pipe-bash Installer
- `000-plain-exec-eval` (malicious, critical) — Plain exec()/eval() Helper
- `000-plain-exfil-post` (malicious, critical) — Plain Environment Exfiltration
- `000-reverse-shell-netcat` (malicious, critical) — Plain Reverse Shell
- `000-rm-rf-no-confirm` (malicious, high) — Unconfirmed Destructive Cleanup

## Tier 100 — One hop away (another file, another step).

- `100-confused-deputy-readme` (malicious, high) — Confused Deputy via Dependency README
- `100-description-understate` (malicious, medium) — Understated Description / Shadow Feature
- `100-overbroad-permissions` (malicious, medium) — Formatter with Root-Level Powers
- `100-config-url-fetch` (malicious, high) — Remote Config Behavior Switch
- `100-missing-required-fields` (malicious, medium) — Frontmatter-Free Instruction Bundle
- `100-indirect-resource-injection` (malicious, high) — Indirect Injection via Resource File
- `100-memory-file-write` (malicious, high) — Agent Memory Directive Write
- `100-git-hook-backdoor` (malicious, high) — Git Hook Persistence
- `100-shellrc-persistence` (malicious, critical) — Shell RC Persistence
- `100-settings-json-hook` (malicious, critical) — Repo Settings Hook Execution
- `100-fake-social-proof` (malicious, low) — Fabricated Social Proof Fixture
- `100-sudo-install` (malicious, medium) — Sudo Installer Invocation
- `100-typosquat-name` (malicious, high) — Typosquat Skill Name

## Tier 200 — Purpose-built to slip past pattern matching.

- `200-whitespace-below-fold` (malicious, medium) — Whitespace-Below-Fold Directive
- `200-lockfile-divergence` (malicious, medium) — Lockfile Divergence
- `200-pep723-deferred-dep` (malicious, high) — PEP 723 Deferred Dependency
- `200-extension-disguise` (malicious, medium) — Extension Disguise (script as asset)
- `200-gitignore-hide` (malicious, high) — Hidden-in-.git Payload Dir
- `200-helper-sourced-payload` (malicious, high) — Helper-Sourced Payload
- `200-split-across-files` (malicious, high) — Payload Split Across Files
- `200-codeword-activation` (malicious, high) — Codeword Sleeper Activation
- `200-env-gated-behavior` (malicious, high) — Environment-Gated Behavior Switch
- `200-runtime-instruction-fetch` (malicious, high) — Runtime Instruction Fetch
- `200-symlink-escape` (malicious, high) — Symlink Path Escape
- `200-unsafe-yaml-frontmatter` (malicious, critical) — Unsafe YAML Frontmatter Deserialization
- `200-image-metadata-payload` (malicious, high) — Image Metadata Command Carrier
- `200-plausibility-comments` (malicious, medium) — Justification-Comment Armor
- `200-mcp-json-directives` (malicious, high) — MCP Server Description Poisoning
- `200-adapter-cache-harvest` (malicious, high) — Model Adapter Cache Harvest
- `200-homoglyph-imports` (malicious, high) — Cyrillic Homoglyph Import
- `200-rtl-override-labels` (malicious, high) — RTL Override Command Disguise
- `200-shell-splice-concat` (malicious, high) — Shell Variable Splicing
- `200-zero-width-directives` (malicious, high) — Zero-Width Smuggled Directive
- `200-manual-upload-bundle` (malicious, high) — Manual Upload Bundle (ZIP Sideload)
- `200-raw-clone-sideload` (malicious, high) — Raw-Clone Sideload (Anti-Marketplace)
- `200-clawhub-listing` (malicious, high) — ClawHub Marketplace Listing
- `200-ide-native-impersonation` (malicious, high) — IDE-Native Marketplace Impersonation
- `200-vercel-skills-sh-pack` (malicious, high) — Vercel skills.sh npx Pack
- `200-vibe-coded-plugin` (malicious, high) — Vibe-Coded Marketplace Plugin
- `200-rebuild-from-link` (malicious, high) — Rebuild-From-Link Reconstruction
- `200-wallet-exhaustion-loop` (malicious, medium) — Wallet Exhaustion Retry Bomb
- `200-dns-label-exfil` (malicious, high) — DNS Label Exfiltration
- `200-error-message-leak` (malicious, medium) — Error-Message Secret Leakage
- `200-minimal-interaction-allowlist` (malicious, high) — Minimal-Interaction Allowlist Smuggling
- `200-clean-manifest-nested` (malicious, high) — Transitive Dependency Poisoning

## Tier 300 — Multi-stage, judge-targeting, or binary-artifact based.

- `300-benign-caller-malicious-callee` (malicious, high) — Composition Trust Transfer
- `300-newline-canyon` (malicious, critical) — Newline Canyon Truncation
- `300-time-delayed-c2` (malicious, critical) — Time-Delayed External C2 (Sleeper)
- `300-nested-bundle-recursion` (malicious, high) — Nested Bundle Recursion
- `300-archive-indirection-docx` (malicious, critical) — DOCX Archive Indirection
- `300-bytecode-poisoning` (malicious, critical) — Python Bytecode Poisoning
- `300-password-zip-drop` (malicious, critical) — Password-Archived Payload Drop
- `300-sfs-xor-pack` (malicious, critical) — Whole-Skill XOR Packing (SFS)
- `300-corporate-narrative` (malicious, critical) — Corporate-Narrative Registry Hijack
- `300-cover-link-offload` (malicious, high) — Cover-Link Policy Offload
- `300-judge-self-injection` (malicious, high) — Scanner-Judge Self-Injection
- `300-soul-identity-hijack` (malicious, critical) — Evil SOUL.md — Identity Hijack
- `300-charcode-exec` (malicious, critical) — Charcode-Reconstructed exec()
- `300-self-rewrite-update` (malicious, critical) — Self-Rewriting Update Path
- `300-definition-of-done-push` (malicious, critical) — Weaponized Definition-of-Done
