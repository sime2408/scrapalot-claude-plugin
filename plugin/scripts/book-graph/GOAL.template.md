# GOAL — the standing instruction for the unattended graph sweep

Build and verify the knowledge graph of the corpus, ONE book at a time, in the
`books` workspace first and the rest afterwards, until every parse-clean book in
a tier-2 collection has a graph a fresh critic has accepted.

The bar for a book is the book: a critic with no context, given the entity
material read out of the text and the entity names stored in the graph
unlabelled, must say they are the same book's. "Mostly" is a no.

Run only in DeepSeek's off-peak hours, and only while there is room on the disk:
`scripts/book-graph/disk-check.sh` before every book and before every build. At
88% on the volume Neo4j and pgvector share, stop the sweep — mid-book if that is
where it is — and tell the owner.

Stop and tell the owner when the disk is nearly full, when the account runs out
of money, when the sweep is finished, or when two different fixes hit the same
gap.

Decide code fixes yourself: isolated worktree, feature branch, PR with the
measurement, `scrapalot:devops-verifier` review until two consecutive APPROVE
rounds, then merge. Reprocessing documents, Neo4j writes beyond the orchestrated
build, and workspace-wide dispatches stay the owner's call — ask, do not act.

After every book, sharpen the command itself (Phase 6): whatever the critic
caught that no check asked about, whatever check went green over a broken
outcome, whatever you had to work out by hand — turn it into an edit of
`/scrapalot:book-graph`, with the measurement in the commit message. Sharpen how
it sees; never loosen what it must do.

Write what happened to `.claude/postprocess/progress.txt` (one row per book) and
keep `STATE.md` next to this file current enough that a cold session can resume.
