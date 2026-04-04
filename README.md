# Bradbury Oracle

A decentralized oracle built on GenLayer that resolves YES/NO prediction market questions by searching the web in real time.

## What is this?

One of the hardest problems in prediction markets is resolving them fairly  who decides if something happened or not? This project tackles that by using GenLayer's Intelligent Contracts to fetch real web data and let an AI determine the outcome, with multiple validators having to agree before anything is finalized.

Built for the Bradbury Special Track of the GenLayer Hackathon.

## How it works

1. Someone submits a YES/NO question with a URL where the answer can be found
2. When `resolve` is called, the contract fetches the page and passes it to an LLM
3. The LLM reads the content and answers YES, NO, or UNDETERMINED
4. Multiple GenLayer validators independently do the same thing
5. If they agree → the answer is finalized on-chain

## Example

```
Question: Did Argentina win the 2022 FIFA World Cup?
URL: https://en.wikipedia.org/wiki/2022_FIFA_World_Cup_Final

Result: YES (95% confidence)
Reasoning: Argentina were confirmed as champions according to Wikipedia
```

## Why UNDETERMINED matters

If the source page doesn't have enough information, the oracle honestly returns UNDETERMINED instead of guessing. This is important for a trustless system  better to admit uncertainty than give a wrong answer.

## Built with

- GenLayer Studio
- Python (GenLayer Intelligent Contract SDK)
- `gl.vm.run_nondet_unsafe` for Equivalence Principle
- Optimistic Democracy consensus

## Functions

- `submit_question(question, resolution_url)`  add a new question
- `resolve(question_id)`  trigger AI resolution
- `get_question(question_id)`  see result and reasoning
- `get_oracle_summary()`  overall stats
- `batch_submit(...)`  submit 3 questions at once

## How to run it

1. Go to [GenLayer Studio](https://studio.genlayer.com)
2. Create a new file and paste `bradbury_oracle.py`
3. Set execution mode to Normal (Full Consensus)
4. Deploy with your address as `owner_address`
5. Call `submit_question` then `resolve`

## Notes

This is part of the GenLayer Incentivized Builder Program, Bradbury Special Track. The oracle uses Wikipedia as the primary data source since it's reliable and accessible to all validators consistently.
