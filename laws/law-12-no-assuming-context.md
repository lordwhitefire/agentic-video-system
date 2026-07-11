# Law 12: No Assuming Context

An agent's reasoning must not reference information not present in the current run's inputs. If the agent uses external knowledge, it must flag it as "external_context" and request user permission.

**Applies to:** All agents.
**Example:** Agent does not apply knowledge from its training data about Mbappé without flagging it as external and asking the user.
