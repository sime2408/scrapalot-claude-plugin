---
description: Review a scrapalot-chat feature branch end to end and open the PR if it is not open yet.
---

# Pull request agent review

1. You are given a feature branch name: $ARGUMENTS that you should review.
2. Check if you're already on that branch, if not checkout: `gh pr checkout [id]`
If the user does not have the gh CLI, use git commands with users' ssh key (see ~/.ssh/config).

3. If PR is not open, please open it. When creating new PR, your commit message should not contain icons, and should explain changes in that feature.

4. REVIEW INSTRUCTIONS: You are a senior Architect, and FULL-STACK  developer reviewing pull requests.
Please deep code review this branch against origin and fix bugs. Perform the same approach 5 times, or unless all bugs are fixed and you're satisfied with the code style! Use latest code styles - for examples: lambdas, walrus operators, less try catch and if else.
Then, check if local commits needs to be squashed or if only one commit then you can amend, then ask user if you can force push the squashed changes.
If local branch is identical as remote, that means we already merged the changes, and you can skip the review.

5. After all code is fixed are processed, summarize what you did, and which comments need more attention.
6. Try to resolve open comments and again run search for remaining stuff to finish!
7. If not previously, ask user to push the changes by squashing commits and force pushing to have single commit on that PR for review!
