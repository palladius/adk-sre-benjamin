## Dos and DONTs

Never overwrite .env file without asking.
Never check in .env in git!!

## Coding

* Use worktree to work on GH Issue and work in parallel in .worktrees/ . Use worktree HITL Conductor skill if available.
* Use conductor for features.
* When adding features, keep `CHANGELOG.md` updated and bump versions by 0.0.1 each time so we can track in the UI
  the progress. Bump by 010 and 100 for major and breaking changes (SemVer).

## UI

* The UI should be minimal.

## Usability/Docs

Ensure all features are documented in:

* `doc/USER_MANUAL.md` from the pov of a user
* `README.md` very shortly as features set.

## Intake from GH Issues

Occasionally keep an eye on https://github.com/palladius/adk-sre-benjamin/issues/XX
* use `gh` to check them.
* If you havent done it, use the /conductor:newTrack to track their content (and update GHI with the track name/id)
* Update the GHI with progress as milestones get delivered.
* Close ticket when done.
* Link git commits to GHI.
* ALWAYS Sign yourself with your harness name and the github user you use, (eg `-- from agy CLI on behalf of Riccardo"`.
  This is important since you're using a logged in account which is probably the SAME person who reads you!
  Also use plenty of emojis (ie, roughly one per line of text), which the user usually doesn't do.
* Add a bit of explaination of what you do/did. its always good to have a compact explaination of the problem to solve,
  and how you solved it, for posterity.
