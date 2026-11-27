# Launch and adoption

Lead with a reproducible SQLite-to-CSV handoff. Run the demo, copy two small files, and show a same-count mismatch. The expected path is under a minute for users who already have Python. For the first release, publish the zipapp, wheel, source and hashes on GitHub when a repository owner is available. Keep first use offline and independent of account creation.

## First pilots

Reach maintainers of embedded SQLite applications, backup and restore tooling, migration libraries and edge products. Candidate conversations include Litestream and django-litestream maintainers, Room and Datasette users, Turso engineers, self-hosting operators, and edge software teams already moving SQLite or CSV exports. These are prospective users with relevant workflows.

- Offer the local demo and a fixture in [r/sqlite](https://www.reddit.com/r/sqlite/), [r/selfhosted](https://www.reddit.com/r/selfhosted/), and [r/dataengineering](https://www.reddit.com/r/dataengineering/) if community rules permit the submission.
- Submit a Show HN demonstration with commands, a benchmark and the receipt privacy model. Post to the [SQLite forum](https://sqlite.org/forum/) after verifying the SQLite-specific integration. Seek a technical write-up for [DB Weekly](https://dbweekly.com/) or [LWN](https://lwn.net/) after practitioners have tested the workflow.
- Contribute a backup/restore CI example to interested SQLite communities. Propose a recipe for Datasette or a Litestream integration that captures a pre-backup and post-restore app table at an agreed cutoff. Explore listings in [awesome-sqlite](https://github.com/planetopendata/awesome-sqlite) after a stable public release meets directory criteria. Use Product Hunt if the technical demo has traction with independent developers.

## Growth loop

Each accepted adapter or application recipe increases the number of receipt pairs people can compare. Versioned fixtures let independent tools participate without coupling their release cycle to the Python CLI. One successful handoff can become a repository check or recurring restore check, which exposes the same tool to the next export or destination maintainer.

Collect opt-in issues, integration PRs, confirmed successful pilot comparisons, recurring use, and setup time. The CLI has no telemetry. Look for three teams that independently choose to reuse it for a second comparison before spending heavily on adapters. Contact maintainers individually with a reproduction relevant to their project and follow each community's submission norms.
