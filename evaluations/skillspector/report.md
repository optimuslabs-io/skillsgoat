# Evaluation matrix — skillspector

- scanned_at: 2026-09-03T00:54:36.265947+00:00
- llm_enabled: False
- caught (block-threshold): **8**
- weak-flagged (detected, below block): **34**
- bypassed (zero detection): **18**
- benign_fp_rate: **0.6**

| Entry | Ground truth | Result | Scanner |
|---|---|---|---|
| admin-installer | benign | FP-WEAK | 35 MEDIUM CAUTION (3 issues) |
| base64-logo-asset | benign | CLEAN | 0 LOW SAFE (0 issues) |
| cjk-documentation | benign | FP-WEAK | 5 LOW SAFE (1 issues) |
| env-names-only | benign | FP-WEAK | 7 LOW CAUTION (1 issues) |
| example-code-exec | benign | CLEAN | 0 LOW CAUTION (0 issues) |
| git-hooks-legit | benign | FP-WEAK | 16 LOW SAFE (2 issues) |
| long-legitimate | benign | CLEAN | 0 LOW SAFE (0 issues) |
| registry-mirror-documented | benign | CLEAN | 0 LOW CAUTION (0 issues) |
| security-doc-explains-attacks | benign | FP-WEAK | 42 MEDIUM CAUTION (2 issues) |
| ssh-config-reader | benign | FP-WEAK | 36 MEDIUM CAUTION (2 issues) |
| 000-base64-obvious | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 000-bcc-exfil | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 000-env-harvest-loop | malicious | WEAK-FLAG | 29 MEDIUM CAUTION (2 issues) |
| 000-hidden-html-comment-instruction | malicious | WEAK-FLAG | 17 LOW CAUTION (1 issues) |
| 000-ignore-previous-instructions | malicious | CAUGHT | 67 HIGH DO_NOT_INSTALL (4 issues) |
| 000-plain-curl-bash | malicious | WEAK-FLAG | 40 MEDIUM CAUTION (2 issues) |
| 000-plain-exec-eval | malicious | CAUGHT | 93 CRITICAL DO_NOT_INSTALL (3 issues) |
| 000-plain-exfil-post | malicious | CAUGHT | 57 HIGH DO_NOT_INSTALL (5 issues) |
| 000-reverse-shell-netcat | malicious | CAUGHT | 55 HIGH DO_NOT_INSTALL (1 issues) |
| 000-rm-rf-no-confirm | malicious | CAUGHT | 54 HIGH DO_NOT_INSTALL (3 issues) |
| 300-benign-caller-malicious-callee | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 100-confused-deputy-readme | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 200-whitespace-below-fold | malicious | WEAK-FLAG | 31 MEDIUM CAUTION (3 issues) |
| 300-newline-canyon | malicious | WEAK-FLAG | 35 MEDIUM CAUTION (2 issues) |
| 200-lockfile-divergence | malicious | WEAK-FLAG | 7 LOW CAUTION (1 issues) |
| 200-pep723-deferred-dep | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 100-description-understate | malicious | WEAK-FLAG | 42 MEDIUM CAUTION (3 issues) |
| 200-extension-disguise | malicious | WEAK-FLAG | 7 LOW SAFE (1 issues) |
| 200-gitignore-hide | malicious | WEAK-FLAG | 37 MEDIUM CAUTION (2 issues) |
| 200-helper-sourced-payload | malicious | WEAK-FLAG | 22 MEDIUM CAUTION (1 issues) |
| 200-split-across-files | malicious | WEAK-FLAG | 31 MEDIUM CAUTION (2 issues) |
| 200-codeword-activation | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 200-env-gated-behavior | malicious | WEAK-FLAG | 45 MEDIUM CAUTION (3 issues) |
| 100-overbroad-permissions | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 100-config-url-fetch | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 100-missing-required-fields | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 200-symlink-escape | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 200-unsafe-yaml-frontmatter | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 300-nested-bundle-recursion | malicious | WEAK-FLAG | 16 LOW SAFE (2 issues) |
| 200-image-metadata-payload | malicious | CAUGHT | 82 CRITICAL DO_NOT_INSTALL (5 issues) |
| 300-archive-indirection-docx | malicious | CAUGHT | 64 HIGH DO_NOT_INSTALL (3 issues) |
| 300-bytecode-poisoning | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 300-password-zip-drop | malicious | WEAK-FLAG | 6 LOW CAUTION (1 issues) |
| 300-sfs-xor-pack | malicious | WEAK-FLAG | 37 MEDIUM CAUTION (3 issues) |
| 100-indirect-resource-injection | malicious | WEAK-FLAG | 40 MEDIUM CAUTION (2 issues) |
| 200-plausibility-comments | malicious | WEAK-FLAG | 25 MEDIUM CAUTION (3 issues) |
| 300-corporate-narrative | malicious | WEAK-FLAG | 22 MEDIUM CAUTION (1 issues) |
| 300-judge-self-injection | malicious | WEAK-FLAG | 15 LOW CAUTION (1 issues) |
| 200-mcp-json-directives | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 100-memory-file-write | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 300-soul-identity-hijack | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 200-adapter-cache-harvest | malicious | WEAK-FLAG | 33 MEDIUM CAUTION (2 issues) |
| 200-homoglyph-imports | malicious | WEAK-FLAG | 13 LOW SAFE (2 issues) |
| 200-rtl-override-labels | malicious | WEAK-FLAG | 41 MEDIUM CAUTION (2 issues) |
| 200-shell-splice-concat | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 200-zero-width-directives | malicious | WEAK-FLAG | 42 MEDIUM CAUTION (4 issues) |
| 300-charcode-exec | malicious | WEAK-FLAG | 4 LOW SAFE (2 issues) |
| 100-git-hook-backdoor | malicious | WEAK-FLAG | 7 LOW SAFE (1 issues) |
| 100-shellrc-persistence | malicious | WEAK-FLAG | 7 LOW SAFE (1 issues) |
| 100-settings-json-hook | malicious | WEAK-FLAG | 7 LOW CAUTION (1 issues) |
| 100-fake-social-proof | malicious | BYPASSED | 0 LOW CAUTION (0 issues) |
| 200-wallet-exhaustion-loop | malicious | WEAK-FLAG | 7 LOW SAFE (1 issues) |
| 300-self-rewrite-update | malicious | CAUGHT | 56 HIGH DO_NOT_INSTALL (3 issues) |
| 200-dns-label-exfil | malicious | WEAK-FLAG | 29 MEDIUM CAUTION (1 issues) |
| 200-error-message-leak | malicious | WEAK-FLAG | 29 MEDIUM CAUTION (2 issues) |
| 200-minimal-interaction-allowlist | malicious | BYPASSED | 0 LOW SAFE (0 issues) |
| 300-definition-of-done-push | malicious | WEAK-FLAG | 20 LOW SAFE (1 issues) |
| 100-sudo-install | malicious | WEAK-FLAG | 13 LOW SAFE (2 issues) |
| 200-clean-manifest-nested | malicious | WEAK-FLAG | 45 MEDIUM CAUTION (1 issues) |
| 100-typosquat-name | malicious | WEAK-FLAG | 40 MEDIUM CAUTION (2 issues) |
