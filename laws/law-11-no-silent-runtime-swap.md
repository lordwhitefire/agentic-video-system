# Law 11: No Silent Runtime Swap

The Editor does not silently switch rendering runtimes (HyperFrames vs Remotion) because one is faster. OpenMontage's decision matrix routes the brief. Editor follows the routing.

**Applies to:** Editor agent.
**Enforcement:** Watcher/Blocker monitors for runtime swaps.
