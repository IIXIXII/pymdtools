# Security policy

Security fixes target the latest stable release. Upgrade to the latest patch
release before reporting an issue. The next release requires Python 3.11 or
newer; Python 3.10 users can continue using 2.1.1, but should migrate to a
supported Python version to receive future fixes.

Report suspected vulnerabilities privately using
[GitHub's vulnerability reporting form](https://github.com/IIXIXII/pymdtools/security/advisories/new).
If private reporting is unavailable, email florent.tournois@gmail.com with
the subject `pymdtools security report`. Do not post exploit details in public
issues before the maintainer has reviewed them.

Include the affected version, Python version, operating system, a minimal
reproducer and the impact. Remove credentials and private document content.
The maintainer will assess the report and coordinate a fix and disclosure;
there is no guaranteed response deadline.

Include lookup rejects absolute paths and parent traversal in filenames.
`nb_up_path` explicitly broadens the permitted search roots; leave it at zero
when processing documents whose includes must stay in their configured roots.
The default PDF renderer disables JavaScript and network access. Enabling
network access or rendering trusted raw HTML changes these boundaries.
See the documentation's rendering and resource-policy sections for details.
