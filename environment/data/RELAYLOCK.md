# Relay-lock level specification

Level JSON fields:

```json
{"length":6,"start":{"player":0,"crate":1,"dial":"N","key":false},"conveyor":1,"ice":[2,3],"plate":4,"key_position":5,"goal":5,"target_dial":"E"}
```

Positions are integers from `0` through `length-1`. The player moves one cell and cannot enter the crate. `turn clockwise` changes N→E→S→W→N; counterclockwise reverses it. `push east` requires the player immediately west of the crate and moves the crate one cell east; the player remains in the same cell.

After every command, phases occur in this order: primary action; forced crate sliding; conveyor movement; plate update; item/goal checks. Forced sliding moves the crate east while the crate is on ice and the east cell is in bounds and not occupied by the player; each one-cell slide adds one wear. Conveyor movement only happens for dial `E` or `W`, moves the crate exactly one cell in that direction if the destination is in bounds and not occupied by the player, and does not trigger additional ice sliding. Because sliding is resolved before conveyors, a crate that finishes sliding onto a conveyor still uses that conveyor later in the same command. A plate opens the route to the key when the crate occupies it. While that route is closed, the player cannot enter `key_position`. `take key` requires the player at `key_position` and no key already held. `use key` requires the player at `goal`, the key, the crate on the plate, and the target dial. `wait` has no primary action but still runs all post-command phases.

This document is the complete rules source for the puzzle. The public examples illustrate these rules but do not add hidden semantics. A legal route can still be noncanonical because pushes and ice-wear are graded after command count.
